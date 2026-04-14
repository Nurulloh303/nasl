import logging
import os

from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import Profile

from .models import PromoCode
from .serializers import ActivatePromoCodeSerializer

logger = logging.getLogger(__name__)


class ActivatePromoView(APIView):
    """
    Promokodni faollashtirish.

    POST /api/v1/promo/activate/
    Body: {"code": "ABCD1234"}

    Foydalanuvchi promokodni yuborganda:
    1. Kod tekshiriladi (mavjudligi, faolligi)
    2. Foydalanuvchi balansiga tokenlar qo'shiladi
    3. Kod is_active=False qilinadi
    """

    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        serializer = ActivatePromoCodeSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)

        promo = serializer.context["promo"]

        # Promokodni qayta SELECT FOR UPDATE bilan qulflash (race condition oldini olish)
        promo = PromoCode.objects.select_for_update().get(pk=promo.pk)

        # Ikki marta tekshirish (concurrent request bo'lishi mumkin)
        if not promo.is_active:
            return Response(
                {"error": "Bu promokod allaqachon ishlatilgan."},
                status=status.HTTP_409_CONFLICT,
            )

        # Foydalanuvchi profilini qulflash
        profile = Profile.objects.select_for_update().get(user=request.user)

        # Tokenlarni qo'shish
        profile.credits += promo.token_count
        if profile.credits > 0:
            profile.plan = Profile.PLAN_PRO
        profile.save(update_fields=["credits", "plan"])

        # Promokodni ishlatilgan deb belgilash
        promo.is_active = False
        promo.used_by = request.user
        promo.used_at = timezone.now()
        promo.save(update_fields=["is_active", "used_by", "used_at"])

        logger.info(
            "Promo activated: code=%s user=%s tokens=%s",
            promo.code,
            request.user.id,
            promo.token_count,
        )

        return Response(
            {
                "message": "Promokod muvaffaqiyatli faollashtirildi!",
                "tokens_added": promo.token_count,
                "total_credits": profile.credits,
                "plan": profile.plan,
            },
            status=status.HTTP_200_OK,
        )


class PackagesView(APIView):
    """
    Mavjud to'lov paketlarini ko'rsatish.

    GET /api/v1/promo/packages/

    Javobda admin karta raqami va Telegram linki ham qaytariladi.
    """

    permission_classes = [AllowAny]

    # .env dan yoki default qiymatlardan olinadi
    ADMIN_CARD_NUMBER = os.getenv("ADMIN_CARD_NUMBER", "9860 6067 5148 3557")
    ADMIN_TELEGRAM_LINK = os.getenv("ADMIN_TELEGRAM_LINK", "https://t.me/onlyforwardarch")

    def get(self, request):
        packages = []
        for amount, label in PromoCode.PACKAGE_CHOICES:
            token_count = PromoCode.AMOUNT_TOKEN_MAP.get(amount, 0)
            packages.append(
                {
                    "amount": amount,
                    "label": label,
                    "token_count": token_count,
                }
            )

        return Response(
            {
                "packages": packages,
                "payment_info": {
                    "card_number": self.ADMIN_CARD_NUMBER,
                    "telegram_link": self.ADMIN_TELEGRAM_LINK,
                    "instruction": (
                        "1. Yuqoridagi paketlardan birini tanlang.\n"
                        "2. Karta raqamiga to'lovni amalga oshiring.\n"
                        "3. To'lov chekini Telegram orqali yuboring.\n"
                        "4. Admin promokodni yuboradi.\n"
                        "5. Promokodni kiritib balansni to'ldiring."
                    ),
                },
            },
            status=status.HTTP_200_OK,
        )


class BotGeneratePromoView(APIView):
    """
    Bot orqali yangi promokod yaratish uchun maxfiy API.

    POST /api/v1/promo/bot-generate/
    Headers: {"X-Bot-Token": "secret_token_from_env"}
    Body: {"amount": 22000}
    """

    permission_classes = [AllowAny]  # Custom auth orqali tekshiramiz

    def post(self, request):
        # 1. Botni autentifikatsiya qilish
        expected_token = os.getenv("BOT_SECRET_TOKEN", "default_secret_for_bot_123")
        provided_token = request.headers.get("X-Bot-Token")

        if not provided_token or provided_token != expected_token:
            return Response(
                {"error": "Ruxsat etilmagan. Noto'g'ri token."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # 2. Summani olish
        amount = request.data.get("amount")
        if not amount:
            return Response(
                {"error": "Summa (amount) berilishi shart."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            amount = int(amount)
        except ValueError:
            return Response(
                {"error": "Summa raqam bo'lishi kerak."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 3. Promokod yaratish
        try:
            promo = PromoCode.create_promo(amount)
            return Response(
                {
                    "message": "Promokod yaratildi",
                    "code": promo.code,
                    "amount": promo.amount,
                    "token_count": promo.token_count,
                },
                status=status.HTTP_201_CREATED,
            )
        except ValueError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

