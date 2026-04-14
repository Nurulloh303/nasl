from django.urls import path
from .payment_views import (
    PricingListView,
    InitiatePaymentView,
    CompletePaymentView,
    TransactionHistoryView,
    BuyCreditsDemoView,
)

urlpatterns = [
    path("pricing/", PricingListView.as_view(), name="pricing-list"),
    path("initiate-payment/", InitiatePaymentView.as_view(), name="initiate-payment"),
    path("complete-payment/", CompletePaymentView.as_view(), name="complete-payment"),
    path("transactions/", TransactionHistoryView.as_view(), name="transactions"),
    path("buy-demo/", BuyCreditsDemoView.as_view(), name="buy-demo"),  # Demo uchun
]
