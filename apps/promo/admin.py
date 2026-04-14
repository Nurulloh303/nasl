from django import forms
from django.contrib import admin, messages

from .models import PromoCode


@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "amount",
        "token_count",
        "is_active",
        "used_by",
        "used_at",
        "created_at",
    )
    list_filter = ("is_active", "amount", "created_at")
    search_fields = ("code", "used_by__username")
    readonly_fields = ("code", "used_by", "used_at", "created_at")
    ordering = ("-created_at",)

    actions = [
        "deactivate_codes",
        "generate_22k",
        "generate_50k",
        "generate_110k",
    ]

    # ─── Promokod generatsiya actionlar ───────────────────────────────────

    @admin.action(description="➕ Yangi promokod yaratish — 22 000 so'm (50 token)")
    def generate_22k(self, request, queryset):
        self._generate(request, amount=22_000)

    @admin.action(description="➕ Yangi promokod yaratish — 50 000 so'm (110 token)")
    def generate_50k(self, request, queryset):
        self._generate(request, amount=50_000)

    @admin.action(description="➕ Yangi promokod yaratish — 110 000 so'm (250 token)")
    def generate_110k(self, request, queryset):
        self._generate(request, amount=110_000)

    def _generate(self, request, amount):
        try:
            promo = PromoCode.create_promo(amount)
            messages.success(
                request,
                f"✅ Promokod yaratildi: {promo.code} "
                f"({promo.amount} so'm — {promo.token_count} token)",
            )
        except ValueError as e:
            messages.error(request, str(e))

    # ─── Deaktivatsiya ────────────────────────────────────────────────────

    @admin.action(description="❌ Tanlangan kodlarni deaktivatsiya qilish")
    def deactivate_codes(self, request, queryset):
        updated = queryset.filter(is_active=True).update(is_active=False)
        messages.success(request, f"{updated} ta promokod deaktivatsiya qilindi.")
