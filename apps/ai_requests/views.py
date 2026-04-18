import requests
from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import GenerationRequest
from .prompt_dispatcher import build_prompt
from .serializers import GenerationRequestSerializer, GenerationSubmitSerializer, PromptPreviewSerializer
from .services import create_generation_request, execute_generation
from .tasks import process_generation_request
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.utils import timezone


class GenerationPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class PromptPreviewView(APIView):
    permission_classes = [AllowAny]
    parser_classes = [JSONParser]

    def post(self, request):
        serializer = PromptPreviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        module = serializer.validated_data["module"]
        data = serializer.validated_data["data"]
        prompt = build_prompt(module, data)
        return Response({"module": module, "prompt": prompt})


class GenerationSubmitView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def post(self, request):
        serializer = GenerationSubmitSerializer(data=request.data)
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

        return Response(GenerationRequestSerializer(gen_request).data, status=status.HTTP_201_CREATED)


class MyGenerationListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = GenerationRequest.objects.filter(user=request.user).order_by("-created_at")
        paginator = GenerationPagination()
        paginated_qs = paginator.paginate_queryset(qs, request)
        serializer = GenerationRequestSerializer(paginated_qs, many=True)
        return paginator.get_paginated_response(serializer.data)


class MyGenerationDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        gen_request = get_object_or_404(GenerationRequest, pk=pk, user=request.user)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_image_view(request):
    """
    KUCHAYTIRILGAN (TANK) PROXY VIEW.
    1. Faqat ro'yxatdan o'tganlar uchun.
    2. Foydalanuvchi balansini tekshiradi va ayiradi.
    3. Google API bilan bog'lanadi.
    4. Har bir so'rovni bazaga qayd qilib boradi.
    """
    user = request.user
    profile = user.profile
    prompt = request.data.get('prompt')

    if not prompt:
        return Response({"error": "Prompt kiritilmagan"}, status=status.HTTP_400_BAD_REQUEST)

    # 1. Balansni tekshirish va band qilish (Reservation)
    token_cost = settings.GENERATION_TOKEN_COST
    reservation = profile.reserve_generation(token_cost)
    
    if reservation["charged_tokens"] == 0 and not reservation["used_free_generation"]:
        return Response({
            "error": "Token yetarli emas yoki limit tugagan. Iltimos, balansni to'ldiring.",
            "required": token_cost,
            "available": profile.credits
        }, status=status.HTTP_402_PAYMENT_REQUIRED)

    # 2. Bazada so'rovni yaratish (Logging uchun)
    gen_request = GenerationRequest.objects.create(
        user=user,
        module="imagen-3-proxy",
        prompt=prompt,
        credits_charged=reservation["charged_tokens"],
        used_free_generation=reservation["used_free_generation"],
        status=GenerationRequest.STATUS_PROCESSING,
        started_at=timezone.now()
    )

    api_key = settings.GEMINI_API_KEY
    google_url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-001:predict?key={api_key}"
    
    payload = {
        "instances": [{"prompt": prompt}],
        "parameters": {"sampleCount": 1}
    }

    try:
        # 3. Googlega so'rov yuboramiz
        response = requests.post(google_url, json=payload, timeout=45)
        response_data = response.json()

        if response.status_code == 200:
            # Muvaffaqiyatli!
            gen_request.status = GenerationRequest.STATUS_COMPLETED
            gen_request.completed_at = timezone.now()
            gen_request.save()
            return Response(response_data, status=status.HTTP_200_OK)
        else:
            # Google xatolik qaytardi
            raise Exception(f"Google API Error: {response.text}")

    except Exception as e:
        # 4. ERROR bo'lsa pulni qaytarish (Rollback mechanism)
        gen_request.status = GenerationRequest.STATUS_FAILED
        gen_request.error_message = str(e)
        gen_request.save()

        # Agar token ishlatilgan bo'lsa, uni qaytarib beramiz
        if reservation["charged_tokens"] > 0:
            profile.refund_generation_tokens(reservation["charged_tokens"])

        return Response({
            "error": "Rasm yaratishda xatolik yuz berdi. Hisobingizdan token yechilmadi.",
            "details": str(e) if settings.DEBUG else "Internal Server Error"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
