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
    KUCHAYTIRILGAN (TANK) PROXY VIEW — Gemini 3.1 Pro Preview.
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

        api_key = settings.GEMINI_API_KEY
        model_name = settings.GEMINI_IMAGE_MODEL
        google_url = (
            f"https://generativelanguage.googleapis.com/v1beta/"
            f"models/{model_name}:generateContent?key={api_key}"
        )

        full_prompt = f"{prompt}. Generate this image with aspect ratio {ratio}."

        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": full_prompt}]
                }
            ],
            "generationConfig": {
                "responseModalities": ["IMAGE", "TEXT"]
            }
        }

        try:
            response = requests.post(google_url, json=payload, timeout=60)

            if response.status_code == 200:
                response_data = response.json()
                image_data = None
                mime_type = "image/png"

                candidates = response_data.get("candidates", [])
                for candidate in candidates:
                    content = candidate.get("content", {})
                    parts = content.get("parts", [])
                    for part in parts:
                        inline_data = part.get("inlineData")
                        if inline_data and inline_data.get("data"):
                            image_data = inline_data["data"]
                            mime_type = inline_data.get("mimeType", "image/png")
                            break
                    if image_data:
                        break

                if image_data:
                    gen_request.status = GenerationRequest.STATUS_COMPLETED
                    gen_request.completed_at = timezone.now()
                    gen_request.save()

                    return Response({
                        "predictions": [
                            {
                                "bytesBase64Encoded": image_data,
                                "mimeType": mime_type
                            }
                        ]
                    }, status=status.HTTP_200_OK)
                else:
                    raise Exception("Google API rasm qaytarmadi. Javob: " + response.text[:300])
            else:
                raise Exception(f"Google API Error ({response.status_code}): {response.text[:500]}")

        except Exception as e:
            gen_request.status = GenerationRequest.STATUS_FAILED
            gen_request.error_message = str(e)[:500]
            gen_request.save()

            if reservation["charged_tokens"] > 0:
                profile.refund_generation_tokens(reservation["charged_tokens"])

            return Response({
                "error": "Rasm yaratishda xatolik yuz berdi. Hisobingizdan token yechilmadi.",
                "details": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
