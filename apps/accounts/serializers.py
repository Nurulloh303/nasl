from django.contrib.auth import authenticate, get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Profile, Transaction

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(write_only=True, required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ("id", "username", "email", "password", "full_name")

    def validate_email(self, value):
        if value and User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Bu email allaqachon mavjud.")
        return value

    def validate_username(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("Bu username allaqachon mavjud.")
        return value

    def create(self, validated_data):
        full_name = validated_data.pop("full_name", "")
        user = User.objects.create_user(**validated_data)
        profile = user.profile
        profile.full_name = full_name or user.username
        profile.save(update_fields=["full_name"])
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(username=attrs["username"], password=attrs["password"])
        if not user:
            raise serializers.ValidationError("Login yoki parol noto'g'ri.")
        attrs["user"] = user
        return attrs


class TelegramAuthSerializer(serializers.Serializer):
    telegram_id = serializers.CharField()
    username = serializers.CharField(required=False, allow_blank=True)
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)
    full_name = serializers.CharField(required=False, allow_blank=True)
    avatar_url = serializers.URLField(required=False, allow_blank=True)

    def validate_telegram_id(self, value):
        if not value:
            raise serializers.ValidationError("telegram_id required")
        return str(value)


class ProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source="user.email", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)
    telegram_id = serializers.CharField(read_only=True)
    free_generations_remaining = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = (
            "username",
            "email",
            "full_name",
            "plan",
            "credits",
            "telegram_id",
            "avatar_url",
            "free_generations_remaining",
            "created_at",
        )

    def get_free_generations_remaining(self, obj):
        return obj.get_free_generations_remaining()


class TransactionHistorySerializer(serializers.ModelSerializer):
    package = serializers.CharField(source="tier.package.name", read_only=True)
    package_icon = serializers.CharField(source="tier.package.icon", read_only=True)
    token_count = serializers.IntegerField(source="tier.token_count", read_only=True)
    generation_count = serializers.IntegerField(source="tier.generation_count", read_only=True)

    class Meta:
        model = Transaction
        fields = (
            "id",
            "package",
            "package_icon",
            "amount_usd",
            "credits_purchased",
            "token_count",
            "generation_count",
            "status",
            "payment_gateway",
            "transaction_id",
            "created_at",
            "completed_at",
        )


class TokenPairSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()
    user = ProfileSerializer()

    @staticmethod
    def for_user(user):
        refresh = RefreshToken.for_user(user)
        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": ProfileSerializer(user.profile).data,
        }
