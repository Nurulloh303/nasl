from django.contrib.auth import get_user_model
from django.db import transaction as db_transaction
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils.crypto import get_random_string

from .serializers import (
    LoginSerializer,
    ProfileSerializer,
    RegisterSerializer,
    TelegramAuthSerializer,
    TokenPairSerializer,
)

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(TokenPairSerializer.for_user(user), status=status.HTTP_201_CREATED)


class LoginView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        return Response(TokenPairSerializer.for_user(user), status=status.HTTP_200_OK)


class TelegramAuthView(APIView):
    permission_classes = [AllowAny]

    @db_transaction.atomic
    def post(self, request):
        serializer = TelegramAuthSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        telegram_id = data["telegram_id"]
        tg_username = data.get("username", "").strip()
        first_name = data.get("first_name", "").strip()
        last_name = data.get("last_name", "").strip()
        avatar_url = data.get("avatar_url", "").strip()
        full_name = (
            data.get("full_name", "").strip()
            or f"{first_name} {last_name}".strip()
            or tg_username
            or f"tg_{telegram_id}"
        )

        existing_user = User.objects.select_related("profile").filter(profile__telegram_id=telegram_id).first()
        if existing_user:
            profile = existing_user.profile
            changed = []
            if full_name and profile.full_name != full_name:
                profile.full_name = full_name
                changed.append("full_name")
            if avatar_url and profile.avatar_url != avatar_url:
                profile.avatar_url = avatar_url
                changed.append("avatar_url")
            if changed:
                profile.save(update_fields=changed)
            return Response(TokenPairSerializer.for_user(existing_user), status=status.HTTP_200_OK)

        username_base = tg_username or f"tg_{telegram_id}"
        username_candidate = username_base
        counter = 1
        while User.objects.filter(username=username_candidate).exists():
            username_candidate = f"{username_base}_{counter}"
            counter += 1

        # Yangi foydalanuvchi uchun tasodifiy parol yaratamiz
        initial_password = get_random_string(length=10)
        user = User.objects.create_user(
            username=username_candidate,
            password=initial_password,
            first_name=first_name,
            last_name=last_name,
        )
        profile = user.profile
        profile.telegram_id = telegram_id
        profile.full_name = full_name
        if avatar_url:
            profile.avatar_url = avatar_url
            profile.save(update_fields=["telegram_id", "full_name", "avatar_url"])
        else:
            profile.save(update_fields=["telegram_id", "full_name"])

        response_data = TokenPairSerializer.for_user(user)
        response_data["initial_password"] = initial_password
        return Response(response_data, status=status.HTTP_201_CREATED)


class MeView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(ProfileSerializer(request.user.profile).data)
