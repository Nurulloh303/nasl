import requests
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.utils import timezone

from rest_framework import status, generics
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import GenerationRequest
from .prompt_dispatcher import build_prompt
from .serializers import (
    GenerationRequestSerializer,
    GenerationSubmitSerializer,
    PromptPreviewSerializer,
    GenerateImageSerializer,
)
from .services import create_generation_request, execute_generation
from .tasks import process_generation_request


class GenerationPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class PromptPreviewView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    parser_classes = [JSONParser]
    serializer_class = PromptPreviewSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        module = serializer.validated_data["module"]
        data = serializer.validated_data["data"]
        prompt = build_prompt(module, data)
        return Response({"module": module, "prompt": prompt})


class GenerationSubmitView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    serializer_class = GenerationSubmitSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        profile = request.user.profile
        token_cost = settings.GENERATION_TOKEN_COST
        reservation = profile.reserve_generation(token_cost)
        if reservation["charged_tokens"] == 0 and not reservation["used_free_generation"]:
            return Response(
                {
                    "error": "Token yetarli emas. Balansni to'ldiring.",
                    "required_tokens": token_cost,
                    "available_tokens": profile.credits,
                    "free_generations_remaining": profile.get_free_generations_remaining(),
                },
                status=status.HTTP_402_PAYMENT_REQUIRED,
            )

        files = request.FILES.getlist("images")
        gen_request = create_generation_request(
            user=request.user,
            module=serializer.validated_data["module"],
            data=serializer.validated_data["data"],
            files=files,
            credits_charged=reservation["charged_tokens"],
            used_free_generation=reservation["used_free_generation"],
        )

        if settings.CELERY_TASK_ALWAYS_EAGER:
            execute_generation(gen_request)
        else:
            process_generation_request.delay(str(gen_request.id))

        response_serializer = GenerationRequestSerializer(gen_request)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class MyGenerationListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = GenerationRequestSerializer
    pagination_class = GenerationPagination

    def get_queryset(self):
        return GenerationRequest.objects.filter(user=self.request.user).order_by("-created_at")


class MyGenerationDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = GenerationRequestSerializer

    def get_queryset(self):
        return GenerationRequest.objects.filter(user=self.request.user)


class GenerateImageView(generics.GenericAPIView):
    """
    KUCHAYTIRILGAN (TANK) PROXY VIEW — Aqlli yo'naltirish (Smart Routing).
    Rasm kelsa -> Segmind (Img2Img). Faqat matn kelsa -> Gemini (Txt2Img).
    """
    permission_classes = [IsAuthenticated]
    serializer_class = GenerateImageSerializer

    def post(self, request, *args, **kwargs):
        user = request.user
        profile = user.profile
        prompt = request.data.get('prompt')
        ratio = request.data.get('ratio', '1:1')
        image_data = request.data.get('image') or request.data.get('imageBase64')

        if not prompt:
            return Response({"error": "Prompt kiritilmagan"}, status=status.HTTP_400_BAD_REQUEST)

        # 1. Balansni tekshirish
        token_cost = settings.GENERATION_TOKEN_COST
        reservation = profile.reserve_generation(token_cost)

        if reservation["charged_tokens"] == 0 and not reservation["used_free_generation"]:
            return Response({
                "error": "Token yetarli emas. Balansni to'ldiring.",
                "required": token_cost,
                "available": profile.credits
            }, status=status.HTTP_402_PAYMENT_REQUIRED)

        # 2. Bazada so'rovni saqlash
        gen_request = GenerationRequest.objects.create(
            user=user,
            module="smart-image-proxy",
            prompt=prompt,
            payload={"ratio": ratio, "has_image": bool(image_data)},
            credits_charged=reservation["charged_tokens"],
            used_free_generation=reservation["used_free_generation"],
            status=GenerationRequest.STATUS_PROCESSING,
            started_at=timezone.now()
        )

        full_prompt = f"{prompt}. Generate this image with aspect ratio {ratio}."
        
        # Rasmni tozalash (data:image/jpeg;base64, qismini olib tashlash)
        clean_base64 = None
        if image_data:
            clean_base64 = image_data.split(",")[-1] if "," in image_data else image_data

        try:
            # ==========================================
            # 1-YO'NALISH: AGAR RASM BO'LSA -> SEGMIND (Img2Img)
            # ==========================================
            if clean_base64:
                segmind_key = settings.SEGMIND_API_KEY
                if not segmind_key:
                     raise Exception("Segmind API kaliti yo'q.")

                url = "https://api.segmind.com/v1/sdxl-img2img"
                payload = {
                    "prompt": full_prompt,
                    "negative_prompt": "ugly, bad resolution, deformed, completely different product, low quality",
                    "image": clean_base64,
                    "strength": 0.85,       # 0.45 ni 0.85 ga o'zgartiring (Fonni keskin almashtirishi uchun)
                    "guidance_scale": 9.0,  # 45% o'zgarish, 55% aslini saqlash
                    "samples": 1,
                    "scheduler": "UniPC",
                    "num_inference_steps": 25,
                    "base64": True
                }
                headers = {"x-api-key": segmind_key, "Content-Type": "application/json"}

                response = requests.post(url, json=payload, headers=headers, timeout=180)
                
                if response.status_code == 200:
                    response_data = response.json()
                    if "image" in response_data:
                        image_result = response_data["image"]
                        provider = "segmind-img2img"
                    else:
                        raise Exception("Segmind rasm qaytarmadi.")
                else:
                    raise Exception(f"Segmind Error: {response.text}")

            # ==========================================
            # 2-YO'NALISH: AGAR RASM BO'LMASA -> GEMINI (Txt2Img)
            # ==========================================
            else:
                api_key = settings.GEMINI_API_KEY
                model_name = settings.GEMINI_IMAGE_MODEL
                google_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:predict?key={api_key}"

                payload = {
                    "instances": [{"prompt": full_prompt}],
                    "parameters": {"sampleCount": 1}
                }
                response = requests.post(google_url, json=payload, timeout=180)

                if response.status_code == 200:
                    response_data = response.json()
                    predictions = response_data.get("predictions", [])
                    if predictions and "bytesBase64Encoded" in predictions[0]:
                        image_result = predictions[0]["bytesBase64Encoded"]
                        provider = "imagen-4.0"
                    else:
                        raise Exception("Google API rasm qaytarmadi.")
                else:
                    raise Exception(f"Google Error: {response.text}")

            # --- MUVAFFAQIYATLI YAKUN ---
            gen_request.status = GenerationRequest.STATUS_COMPLETED
            gen_request.completed_at = timezone.now()
            gen_request.save()

            return Response({
                "predictions": [{"bytesBase64Encoded": image_result, "mimeType": "image/jpeg"}],
                "provider": provider
            }, status=status.HTTP_200_OK)

        except Exception as e:
            # --- XATOLIK VA PULNI QAYTARISH ---
            gen_request.status = GenerationRequest.STATUS_FAILED
            gen_request.error_message = str(e)[:500]
            gen_request.save()

            # MUHIM: Pul qaytarish xatosi tuzatildi!
            if reservation.get("charged_tokens", 0) > 0:
                profile.refund_generation_tokens(reservation["charged_tokens"])

            return Response({
                "error": "AI xizmatida xatolik yuz berdi. Token qaytarildi.",
                "details": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)