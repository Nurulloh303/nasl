import random
import string

from django.conf import settings
from django.db import models


class PromoCode(models.Model):
    """
    Promokod modeli.
    Admin panelda yaratiladi va foydalanuvchi tomonidan faollashtiriladi.
    """

    # Oldindan belgilangan paketlar: (summasi so'mda, token miqdori)
    PACKAGE_CHOICES = [
        (22_000, "22 000 so'm"),
        (50_000, "50 000 so'm"),
        (110_000, "110 000 so'm"),
    ]

    # amount (so'm) -> token_count mapping
    AMOUNT_TOKEN_MAP = {
        22_000: 50,
        50_000: 110,
        110_000: 250,
    }

    code = models.CharField(
        max_length=8,
        unique=True,
        db_index=True,
        editable=False,
        verbose_name="Promokod",
        help_text="Avtomatik yaratilgan 8 xonali kod",
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Summasi (so'm)",
        help_text="Promokod narxi",
    )
    token_count = models.PositiveIntegerField(
        verbose_name="Token miqdori",
        help_text="Foydalanuvchiga beriladigan tokenlar soni",
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        verbose_name="Faolmi",
        help_text="Foydalanilmagan promokod faol bo'ladi",
    )
    used_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="used_promo_codes",
        verbose_name="Ishlatgan foydalanuvchi",
    )
    used_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Ishlatilgan vaqt",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Yaratilgan vaqt",
    )

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "Promokod"
        verbose_name_plural = "Promokodlar"

    def save(self, *args, **kwargs):
        if not self.code:
            # Agar faqat summa kiritilsa, token sonini avtomat topish
            if not self.token_count and self.amount:
                amount_int = int(self.amount)
                if amount_int in self.AMOUNT_TOKEN_MAP:
                    self.token_count = self.AMOUNT_TOKEN_MAP[amount_int]
            self.code = self.generate_unique_code()
        super().save(*args, **kwargs)

    def __str__(self):
        status = "✅ Faol" if self.is_active else "❌ Ishlatilgan"
        return f"{self.code} — {self.amount} so'm ({status})"

    @classmethod
    def generate_unique_code(cls, length=8):
        """Tasodifiy 8 xonali unikal kod yaratish."""
        chars = string.ascii_uppercase + string.digits
        for _ in range(100):  # 100 ta urinish, takrorlanmaslik uchun
            code = "".join(random.choices(chars, k=length))
            if not cls.objects.filter(code=code).exists():
                return code
        raise ValueError("Unikal kod yaratib bo'lmadi. Keyinroq urinib ko'ring.")

    @classmethod
    def create_promo(cls, amount):
        """
        Berilgan summaga mos promokod yaratish.
        amount: so'm miqdori (22000, 50000, 110000)
        """
        token_count = cls.AMOUNT_TOKEN_MAP.get(int(amount))
        if token_count is None:
            raise ValueError(
                f"Noto'g'ri summa: {amount}. "
                f"Mavjud variantlar: {list(cls.AMOUNT_TOKEN_MAP.keys())}"
            )
        code = cls.generate_unique_code()
        return cls.objects.create(
            code=code,
            amount=amount,
            token_count=token_count,
        )
