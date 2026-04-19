from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Profile

User = get_user_model()

@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        # Yangi foydalanuvchiga welcome bonus tokenlar beramiz
        bonus = getattr(settings, "WELCOME_BONUS_TOKENS", 5)
        plan = Profile.PLAN_PRO if bonus > 0 else Profile.PLAN_FREE

        Profile.objects.create(
            user=instance,
            full_name=getattr(instance, "first_name", "") or instance.username,
            credits=bonus,
            plan=plan,
        )
