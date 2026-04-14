from rest_framework import serializers

from .models import PromoCode


class ActivatePromoCodeSerializer(serializers.Serializer):
    """Promokod faollashtirish uchun serializer."""

    code = serializers.CharField(
        max_length=8,
        min_length=8,
        help_text="8 xonali promokod",
    )

    def validate_code(self, value):
        """Kodni tekshirish: mavjudligi va faolligi."""
        code = value.strip().upper()

        try:
            promo = PromoCode.objects.get(code=code)
        except PromoCode.DoesNotExist:
            raise serializers.ValidationError("Promokod topilmadi. Iltimos, tekshirib qaytadan kiriting.")

        if not promo.is_active:
            raise serializers.ValidationError("Bu promokod allaqachon ishlatilgan.")

        self.context["promo"] = promo
        return code


class PromoCodeInfoSerializer(serializers.ModelSerializer):
    """Promokod ma'lumotlarini ko'rsatish uchun serializer."""

    class Meta:
        model = PromoCode
        fields = ("code", "amount", "token_count", "is_active", "created_at")
        read_only_fields = fields
