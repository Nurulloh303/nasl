from django.urls import path

from .views import ActivatePromoView, PackagesView, BotGeneratePromoView

urlpatterns = [
    path("activate/", ActivatePromoView.as_view(), name="promo-activate"),
    path("packages/", PackagesView.as_view(), name="promo-packages"),
    path("bot-generate/", BotGeneratePromoView.as_view(), name="bot-generate-promo"),
]
