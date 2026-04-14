import hashlib
import logging
from urllib.parse import urlencode

from django.conf import settings

logger = logging.getLogger(__name__)


class ClickAdapter:
    def __init__(self):
        self.merchant_id = settings.CLICK_MERCHANT_ID
        self.service_id = settings.CLICK_SERVICE_ID
        self.secret_key = settings.CLICK_SECRET_KEY
        self.callback_url = settings.CLICK_CALLBACK_URL
        self.return_url = settings.CLICK_RETURN_URL
        self.fail_url = settings.CLICK_FAIL_URL
        self.api_url = settings.CLICK_API_URL

    @staticmethod
    def _generate_signature(*parts):
        payload = "".join(str(part) for part in parts)
        return hashlib.sha1(payload.encode("utf-8")).hexdigest()

    def prepare_payment_data(self, transaction):
        amount = int(transaction.amount_usd)
        merchant_trans_id = transaction.id
        sign = self._generate_signature(
            self.merchant_id,
            self.service_id,
            amount,
            merchant_trans_id,
            self.secret_key,
        )
        return {
            "merchant_id": self.merchant_id,
            "service_id": self.service_id,
            "amount": amount,
            "merchant_trans_id": str(merchant_trans_id),
            "description": f"nasl.ai token to'lovi ({transaction.tier.package.name})",
            "merchant_return_url": self.return_url,
            "merchant_fail_url": self.fail_url,
            "click_trans_id": "",
            "sign": sign,
            "account[0][key]": "user_id",
            "account[0][value]": str(transaction.user.id),
        }

    def create_payment_url(self, transaction):
        if not all([self.api_url, self.merchant_id, self.service_id, self.secret_key]):
            return "/api/v1/payment/buy-demo/"
        params = urlencode(self.prepare_payment_data(transaction))
        return f"{self.api_url}?{params}"

    def verify_callback(self, data):
        required = [
            "merchant_id",
            "service_id",
            "amount",
            "merchant_trans_id",
            "click_trans_id",
            "action",
            "error",
            "sign",
        ]
        if not all(key in data for key in required):
            return False

        expected = self._generate_signature(
            data["click_trans_id"],
            data["service_id"],
            data["merchant_trans_id"],
            data["amount"],
            data.get("action", ""),
            data.get("error", ""),
            data["merchant_id"],
            self.secret_key,
        )
        return expected == data["sign"]
