import hashlib
import logging
import requests
from django.conf import settings
from datetime import datetime

logger = logging.getLogger(__name__)


class ClickPaymentAdapter:
    """Click to'lov tizimi uchun adapter."""
    
    def __init__(self):
        self.merchant_id = settings.CLICK_MERCHANT_ID
        self.service_id = settings.CLICK_SERVICE_ID
        self.secret_key = settings.CLICK_SECRET_KEY
        self.api_url = settings.CLICK_API_URL
        self.sandbox = settings.CLICK_SANDBOX
    
    def generate_signature(self, order_id, amount):
        """Click uchun signature yaratish (MD5)."""
        # Click tartibi: merchant_id;service_id;order_id;amount;secret_key
        data = f"{self.merchant_id};{self.service_id};{order_id};{amount};{self.secret_key}"
        signature = hashlib.md5(data.encode()).hexdigest()
        return signature
    
    def create_invoice(self, transaction):
        """
        Click invoice yaratish.
        
        Args:
            transaction: Transaction modeli
        
        Returns:
            {
                "success": True/False,
                "payment_url": "https://...",  # Click checkout sahifasi
                "merchant_trans_id": "...",     # Click transaction ID
                "error": "..."                  # agar xatolik bo'lsa
            }
        """
        try:
            order_id = str(transaction.id)
            amount = transaction.amount_usd
            
            # Signature yaratish
            signature = self.generate_signature(order_id, amount)
            
            # Click API parametrlari
            params = {
                "merchant_id": self.merchant_id,
                "service_id": self.service_id,
                "order_id": order_id,
                "amount": amount,
                "return_url": settings.CLICK_RETURN_URL,
                "cancel_url": settings.CLICK_FAIL_URL,
                "sign_string": signature,
            }
            
            if self.sandbox:
                params["debug"] = 1
            
            # Click to'lov sahifasi URL
            payment_url = self._build_payment_url(params)
            
            logger.info(f"Click invoice created: {order_id}, amount: {amount}")
            
            return {
                "success": True,
                "payment_url": payment_url,
                "merchant_trans_id": order_id,
            }
        
        except Exception as e:
            logger.error(f"Click invoice creation failed: {str(e)}")
            return {
                "success": False,
                "error": f"To'lov asosi yaratishda xatolik: {str(e)}",
            }
    
    def _build_payment_url(self, params):
        """Click checkout URL ni qurish."""
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{self.api_url}?{query_string}"
    
    def verify_callback(self, data):
        """
        Click webhook callback ni tekshirish.
        
        Args:
            data: {
                "click_trans_id": "...",
                "service_id": "...",
                "merchant_trans_id": "...",
                "amount": "...",
                "action": "0" (pending) / "1" (completed),
                "error": "0" (OK) / "1" (ERROR),
                "sign_string": "..."
            }
        
        Returns:
            {
                "success": True/False,
                "transaction_id": "...",
                "status": "completed/failed"
            }
        """
        try:
            # Parametrlarni o'qish
            click_trans_id = data.get("click_trans_id")
            service_id = data.get("service_id")
            merchant_trans_id = data.get("merchant_trans_id")
            amount = data.get("amount")
            action = data.get("action")
            error_code = data.get("error")
            sign_string = data.get("sign_string")
            
            # Service ID tekshirish
            if service_id != str(self.service_id):
                logger.warning(f"Invalid service_id: {service_id}")
                return {
                    "success": False,
                    "error": "Service ID mos kelmadi",
                }
            
            # Signature tekshirish
            expected_signature = self._verify_signature(
                click_trans_id, service_id, merchant_trans_id, amount
            )
            
            if sign_string != expected_signature:
                logger.warning(f"Invalid signature for transaction {merchant_trans_id}")
                return {
                    "success": False,
                    "error": "Signature mos kelmadi",
                }
            
            # Status tekshirish
            if error_code == "0" and action == "1":
                status = "completed"
            else:
                status = "failed"
            
            logger.info(f"Click callback verified: {merchant_trans_id}, status: {status}")
            
            return {
                "success": True,
                "transaction_id": merchant_trans_id,
                "status": status,
                "click_trans_id": click_trans_id,
            }
        
        except Exception as e:
            logger.error(f"Click callback verification failed: {str(e)}")
            return {
                "success": False,
                "error": f"Callback tekshirishda xatolik: {str(e)}",
            }
    
    def _verify_signature(self, click_trans_id, service_id, merchant_trans_id, amount):
        """Click webhook signature ni tekshirish."""
        # Click tartibi: merchant_trans_id;service_id;click_trans_id;amount;secret_key
        data = f"{merchant_trans_id};{service_id};{click_trans_id};{amount};{self.secret_key}"
        return hashlib.md5(data.encode()).hexdigest()


# Singleton instance
click_adapter = ClickPaymentAdapter()
