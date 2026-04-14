from django.conf import settings
from django.db import models, transaction
from django.utils import timezone


class Profile(models.Model):
    PLAN_FREE = "free"
    PLAN_PRO = "pro"
    PLAN_CHOICES = [
        (PLAN_FREE, "Free"),
        (PLAN_PRO, "Pro"),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    full_name = models.CharField(max_length=255, blank=True)
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default=PLAN_FREE)
    active_package = models.ForeignKey(
        "accounts.PricingPackage",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="active_profiles",
    )
    credits = models.PositiveIntegerField(default=0)
    telegram_id = models.CharField(max_length=100, unique=True, null=True, blank=True, db_index=True)
    avatar_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.user.username} ({self.plan})"

    @property
    def is_paid_user(self) -> bool:
        return self.credits > 0 or self.plan == self.PLAN_PRO

    def _completed_generation_count(self) -> int:
        return self.user.generation_requests.filter(status="completed").count()

    def get_free_generations_used(self) -> int:
        return self.user.generation_requests.filter(status="completed", used_free_generation=True).count()

    def get_free_generations_remaining(self) -> int:
        return max(0, settings.FREE_GENERATION_LIMIT - self.get_free_generations_used())

    def can_generate(self, required_tokens: int | None = None) -> bool:
        required_tokens = required_tokens or settings.GENERATION_TOKEN_COST
        return self.credits >= required_tokens or self.get_free_generations_remaining() > 0

    @transaction.atomic
    def reserve_generation(self, required_tokens: int | None = None) -> dict:
        required_tokens = required_tokens or settings.GENERATION_TOKEN_COST
        locked = Profile.objects.select_for_update().get(pk=self.pk)

        if locked.credits >= required_tokens:
            locked.credits -= required_tokens
            if locked.credits == 0:
                locked.plan = self.PLAN_FREE
            locked.save(update_fields=["credits", "plan"])
            self.credits = locked.credits
            self.plan = locked.plan
            return {"charged_tokens": required_tokens, "used_free_generation": False}

        if locked.get_free_generations_remaining() > 0:
            return {"charged_tokens": 0, "used_free_generation": True}

        return {"charged_tokens": 0, "used_free_generation": False}

    @transaction.atomic
    def refund_generation_tokens(self, amount: int) -> None:
        if amount <= 0:
            return
        locked = Profile.objects.select_for_update().get(pk=self.pk)
        locked.credits += amount
        if locked.credits > 0:
            locked.plan = self.PLAN_PRO
        locked.save(update_fields=["credits", "plan"])
        self.credits = locked.credits
        self.plan = locked.plan


class PricingPackage(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "accounts"
        ordering = ("id",)

    def __str__(self):
        return self.name


class PricingTier(models.Model):
    package = models.ForeignKey(PricingPackage, on_delete=models.CASCADE, related_name="tiers")
    amount_usd = models.IntegerField(help_text="Narx so'mda saqlanadi")
    credits_qty = models.PositiveIntegerField(help_text="Token/credit miqdori")
    bonus_percent = models.PositiveIntegerField(default=0)
    order = models.PositiveIntegerField(default=0)
    is_popular = models.BooleanField(default=False)

    class Meta:
        ordering = ("order", "id")
        unique_together = ("package", "amount_usd")
        app_label = "accounts"

    def __str__(self):
        return f"{self.package.name} - {self.amount_usd} so'm"

    @property
    def token_count(self) -> int:
        return self.credits_qty

    @property
    def generation_count(self) -> int:
        cost = max(1, settings.GENERATION_TOKEN_COST)
        return self.credits_qty // cost

    def get_total_credits(self) -> int:
        bonus = (self.credits_qty * self.bonus_percent) // 100
        return self.credits_qty + bonus


class Transaction(models.Model):
    STATUS_PENDING = "pending"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Kutilmoqda"),
        (STATUS_COMPLETED, "Tugallandi"),
        (STATUS_FAILED, "Muvaffaqiyatsiz"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="transactions")
    tier = models.ForeignKey(PricingTier, on_delete=models.PROTECT)
    amount_usd = models.IntegerField()
    credits_purchased = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    payment_gateway = models.CharField(max_length=50, default="click")
    transaction_id = models.CharField(max_length=255, blank=True, null=True, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        app_label = "accounts"
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.user.username} - {self.amount_usd} so'm - {self.status}"

    @transaction.atomic
    def complete(self, gateway_transaction_id: str | None = None):
        locked = Transaction.objects.select_for_update().select_related("user__profile", "tier__package").get(pk=self.pk)
        if locked.status == self.STATUS_COMPLETED:
            return locked

        if gateway_transaction_id and not locked.transaction_id:
            locked.transaction_id = gateway_transaction_id

        locked.status = self.STATUS_COMPLETED
        locked.completed_at = timezone.now()
        locked.save(update_fields=["status", "completed_at", "transaction_id"])

        profile = locked.user.profile
        profile.credits += locked.credits_purchased
        profile.active_package = locked.tier.package
        profile.plan = profile.PLAN_PRO
        profile.save(update_fields=["credits", "active_package", "plan"])
        return locked

    @transaction.atomic
    def fail(self, gateway_transaction_id: str | None = None):
        locked = Transaction.objects.select_for_update().get(pk=self.pk)
        if locked.status == self.STATUS_COMPLETED:
            return locked
        if gateway_transaction_id and not locked.transaction_id:
            locked.transaction_id = gateway_transaction_id
        locked.status = self.STATUS_FAILED
        locked.save(update_fields=["status", "transaction_id"])
        return locked
