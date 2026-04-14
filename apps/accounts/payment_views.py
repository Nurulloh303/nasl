import logging

from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import PricingPackage, PricingTier, Transaction
from .payment_adapters import ClickAdapter
from .serializers import TransactionHistorySerializer

logger = logging.getLogger(__name__)


class PricingListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        packages = PricingPackage.objects.prefetch_related("tiers").all()
        data = []
        for package in packages:
            tiers = []
            for tier in package.tiers.all():
                tiers.append(
                    {
                        "id": tier.id,
                        "amount": tier.amount_usd,
                        "amount_usd": tier.amount_usd,
                        "tokens": tier.token_count,
                        "credits_qty": tier.credits_qty,
                        "bonus_percent": tier.bonus_percent,
                        "total_credits": tier.get_total_credits(),
                        "generations": tier.generation_count,
                        "is_popular": tier.is_popular,
                    }
                )
            data.append(
                {
                    "id": package.id,
                    "name": package.name,
                    "description": package.description,
                    "icon": package.icon,
                    "tiers": tiers,
                }
            )
        return Response(data)


class InitiatePaymentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        tier_id = request.data.get("tier_id")
        if not tier_id:
            return Response({"error": "tier_id required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            tier = PricingTier.objects.select_related("package").get(id=tier_id)
        except PricingTier.DoesNotExist:
            return Response({"error": "Paket topilmadi"}, status=status.HTTP_404_NOT_FOUND)

        transaction = Transaction.objects.create(
            user=request.user,
            tier=tier,
            amount_usd=tier.amount_usd,
            credits_purchased=tier.get_total_credits(),
            status=Transaction.STATUS_PENDING,
            payment_gateway="click",
        )

        adapter = ClickAdapter()
        payment_url = adapter.create_payment_url(transaction)
        logger.info("Transaction initiated id=%s user=%s tier=%s", transaction.id, request.user.id, tier.id)

        return Response(
            {
                "transaction_id": str(transaction.id),
                "amount": tier.amount_usd,
                "tokens": tier.token_count,
                "generations": tier.generation_count,
                "package": tier.package.name,
                "payment_url": payment_url,
                "message": "To'lovni tugallang",
            },
            status=status.HTTP_201_CREATED,
        )


class CompletePaymentView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        adapter = ClickAdapter()
        if not adapter.verify_callback(request.data):
            logger.warning("Invalid Click callback payload=%s", request.data)
            return Response({"error": "Invalid signature"}, status=status.HTTP_400_BAD_REQUEST)

        merchant_trans_id = request.data.get("merchant_trans_id")
        action = str(request.data.get("action", ""))
        error = str(request.data.get("error", ""))
        click_trans_id = request.data.get("click_trans_id")

        try:
            transaction = Transaction.objects.get(id=merchant_trans_id)
        except Transaction.DoesNotExist:
            return Response({"error": "Transaction topilmadi"}, status=status.HTTP_404_NOT_FOUND)

        if error == "0" and action == "1":
            transaction.complete(gateway_transaction_id=click_trans_id)
            logger.info("Payment completed transaction=%s", transaction.id)
            return Response({"message": "To'lov muvaffaqiyatli", "transaction_id": str(transaction.id)})

        transaction.fail(gateway_transaction_id=click_trans_id)
        logger.warning("Payment failed transaction=%s click_trans_id=%s", transaction.id, click_trans_id)
        return Response({"error": "To'lov muvaffaqiyatsiz"}, status=status.HTTP_400_BAD_REQUEST)


class TransactionHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Transaction.objects.select_related("tier__package").filter(user=request.user)
        serializer = TransactionHistorySerializer(qs, many=True)
        return Response(serializer.data)


class BuyCreditsDemoView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        tier_id = request.data.get("tier_id")
        if not tier_id:
            return Response({"error": "tier_id required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            tier = PricingTier.objects.select_related("package").get(id=tier_id)
        except PricingTier.DoesNotExist:
            return Response({"error": "Paket topilmadi"}, status=status.HTTP_404_NOT_FOUND)

        transaction = Transaction.objects.create(
            user=request.user,
            tier=tier,
            amount_usd=tier.amount_usd,
            credits_purchased=tier.get_total_credits(),
            status=Transaction.STATUS_PENDING,
            payment_gateway="demo",
        )
        transaction.complete()

        return Response(
            {
                "message": "Creditlar qo'shildi",
                "credits_added": transaction.credits_purchased,
                "total_credits": request.user.profile.credits,
            }
        )
