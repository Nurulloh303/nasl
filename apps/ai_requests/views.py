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
        return Response(GenerationRequestSerializer(gen_request).data)
