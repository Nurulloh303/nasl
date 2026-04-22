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
    KUCHAYTIRILGAN (TANK) PROXY VIEW — Gemini + Segmind Fallback.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = GenerateImageSerializer

    def post(self, request, *args, **kwargs):
        user = request.user
        profile = user.profile
        prompt = request.data.get('prompt')
        ratio = request.data.get('ratio', '1:1')

        if not prompt:
            return Response({"error": "Prompt kiritilmagan"}, status=status.HTTP_400_BAD_REQUEST)

        # 1. Balansni tekshirish
        token_cost = settings.GENERATION_TOKEN_COST
        reservation = profile.reserve_generation(token_cost)

        if reservation["charged_tokens"] == 0 and not reservation["used_free_generation"]:
            return Response({
                "error": "Token yetarli emas yoki limit tugagan. Iltimos, balansni to'ldiring.",
                "required": token_cost,
                "available": profile.credits
            }, status=status.HTTP_402_PAYMENT_REQUIRED)

        # 2. Bazada so'rovni yaratish
        gen_request = GenerationRequest.objects.create(
            user=user,
            module="gemini-image-proxy",
            prompt=prompt,
            payload={"ratio": ratio},
            credits_charged=reservation["charged_tokens"],
            used_free_generation=reservation["used_free_generation"],
            status=GenerationRequest.STATUS_PROCESSING,
            started_at=timezone.now()
        )

        full_prompt = f"{prompt}. Generate this image with aspect ratio {ratio}."

        # ==========================================
        # 1-URINISH: GEMINI (IMAGEN) API
        # ==========================================
        try:
            api_key = settings.GEMINI_API_KEY
            model_name = settings.GEMINI_IMAGE_MODEL
            
            # DIQQAT: Imagen 4.0 uchun manzil oxiri :predict bilan tugashi shart!
            google_url = (
                f"https://generativelanguage.googleapis.com/v1beta/"
                f"models/{model_name}:predict?key={api_key}"
            )

            # Imagen 4.0 tushunadigan to'g'ri payload formati
            payload = {
                "instances": [
                    {"prompt": full_prompt}
                ],
                "parameters": {
                    "sampleCount": 1
                }
            }

            response = requests.post(google_url, json=payload, timeout=60)

            if response.status_code == 200:
                response_data = response.json()
                predictions = response_data.get("predictions", [])
                
                # Imagen rasmni to'g'ridan-to'g'ri bytesBase64Encoded kalitida qaytaradi
                if predictions and "bytesBase64Encoded" in predictions[0]:
                    image_data = predictions[0]["bytesBase64Encoded"]
                    mime_type = predictions[0].get("mimeType", "image/jpeg")

                    gen_request.status = GenerationRequest.STATUS_COMPLETED
                    gen_request.completed_at = timezone.now()
                    gen_request.save()

                    return Response({
                        "predictions": [
                            {
                                "bytesBase64Encoded": image_data,
                                "mimeType": mime_type
                            }
                        ],
                        "provider": "imagen-4.0"
                    }, status=status.HTTP_200_OK)
                else:
                    raise Exception("Google API rasm qaytarmadi.")
            else:
                raise Exception(f"Google API Error ({response.status_code}): {response.text[:200]}")
        # ==========================================
        # 2-URINISH: SEGMIND API (ZAXIRA)
        # ==========================================
        except Exception as gemini_error:
            print(f"Gemini ishladi, lekin xato berdi: {gemini_error}. Segmind'ga o'tilmoqda...")
            
            try:
                segmind_url = "https://api.segmind.com/v1/ssd-1b"
                segmind_headers = {"x-api-key": getattr(settings, 'SEGMIND_API_KEY', '')}
                segmind_data = {
                    "prompt": full_prompt,
                    "negative_prompt": "blurry, distorted, ugly, bad anatomy",
                    "samples": 1,
                    "base64": True
                }

                segmind_response = requests.post(segmind_url, json=segmind_data, headers=segmind_headers, timeout=60)
                
                if segmind_response.status_code == 200:
                    segmind_image = segmind_response.json().get('image')
                    
                    if segmind_image:
                        # Bazadagi modul nomini o'zgartirib qo'yamiz (tarix uchun)
                        gen_request.module = "segmind-fallback"
                        gen_request.status = GenerationRequest.STATUS_COMPLETED
                        gen_request.completed_at = timezone.now()
                        gen_request.save()

                        return Response({
                            "predictions": [
                                {
                                    "bytesBase64Encoded": segmind_image,
                                    "mimeType": "image/jpeg"
                                }
                            ],
                            "provider": "segmind" # Frontend qaysi AI ishlaganini bilishi uchun
                        }, status=status.HTTP_200_OK)
                    else:
                        raise Exception("Segmind API rasm qaytarmadi.")
                else:
                    raise Exception(f"Segmind Error: {segmind_response.text[:200]}")

            # ==========================================
            # IKKALA API HAM ISHLAMASA
            # ==========================================
            except Exception as segmind_error:
                gen_request.status = GenerationRequest.STATUS_FAILED
                # Ikkala xatoni ham bazaga yozib qo'yamiz
                gen_request.error_message = f"Gemini: {gemini_error} | Segmind: {segmind_error}"[:500]
                gen_request.save()

                # Pulni qaytarish
                if reservation["charged_tokens"] > 0:
                    profile.refund_generation_tokens(reservation["charged_tokens"])

                return Response({
                    "error": "Rasm yaratishda xatolik yuz berdi. Ikkala AI ham ishlamadi. Token yechilmadi.",
                    "details": str(segmind_error)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)