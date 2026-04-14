from django.conf import settings
from django.db import models
from django.utils import timezone


class PricingPackage(models.Model):
    """Har bir module uchun tolov paketlari."""
    
    name = models.CharField(max_length=255)  # "Fashion AI", "Smart Text" kabi
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True)  # emoji yoki icon nomi
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name


class PricingTier(models.Model):
    """Har bir paket ichidagi turli narx variantlari."""
    
    package = models.ForeignKey(PricingPackage, on_delete=models.CASCADE, related_name="tiers")
    
    amount_usd = models.IntegerField()  # 15000 so'm = ~1.3 USD
    credits_qty = models.PositiveIntegerField()  # Beradigan token raqami
    bonus_percent = models.PositiveIntegerField(default=0)  # 20% bonus
    
    order = models.PositiveIntegerField(default=0)
    is_popular = models.BooleanField(default=False)  # Highlighted variant
    
    class Meta:
        ordering = ("order",)
        unique_together = ("package", "amount_usd")
    
    def __str__(self):
        return f"{self.package.name} - {self.amount_usd} so'm"
    
    def get_total_credits(self):
        """Bonus bilan jami credit."""
        bonus = (self.credits_qty * self.bonus_percent) // 100
        return self.credits_qty + bonus


class Transaction(models.Model):
    """To'lov tarixi."""
    
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
    
    payment_gateway = models.CharField(max_length=50, default="payuz")  # Payuz, Click, kabi
    transaction_id = models.CharField(max_length=255, blank=True, unique=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.amount_usd} so'm - {self.status}"
    
    def complete(self):
        """To'lovni tugallash va creditlarni berib yuborish."""
        self.status = self.STATUS_COMPLETED
        self.completed_at = timezone.now()
        self.save(update_fields=["status", "completed_at"])
        
        # Creditlarni qo'shish
        profile = self.user.profile
        profile.credits += self.credits_purchased
        profile.active_package = self.tier.package
        profile.plan = profile.PLAN_PRO
        profile.save(update_fields=["credits", "active_package", "plan"])
