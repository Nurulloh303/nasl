import base64
import logging
import requests
from django.conf import settings

from .base import BaseAIProvider

logger = logging.getLogger(__name__)

class SegmindProvider(BaseAIProvider):
    name = "segmind"

    def __init__(self):
        if not getattr(settings, "SEGMIND_API_KEY", None):
            raise RuntimeError("SEGMIND_API_KEY topilmadi.")
        self.api_key = settings.SEGMIND_API_KEY

    def generate_text(self, prompt: str, data: dict):
        raise NotImplementedError("Segmind is for image generation only.")

    def generate_images(self, prompt: str, image_paths: list[str], output_count: int = 1):
        if not image_paths:
            raise ValueError("Segmind img2img uchun rasm kerak.")

        try:
            from PIL import Image
            import io
            
            # Agar 2 ta rasm kelsa (Masalan, Uslub namunasi va Mahsulot), 
            # asosiysi Mahsulot (ya'ni oxirgi rasm) hisoblanadi.
            # SDXL-img2img faqat bitta rasm qabul qilgani uchun mahsulotni asosiysi qilib olamiz.
            target_image_path = image_paths[-1]
            
            with Image.open(target_image_path) as img:
                # SDXL modeli uchun rasmni optimallashtiramiz (max 1024x1024). 
                # Katta rasmlar jarayonni juda sekinlashtiradi.
                max_size = (1024, 1024)
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
                
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")
                    
                buffer = io.BytesIO()
                img.save(buffer, format="JPEG", quality=85)
                clean_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
        except Exception as e:
            logger.error(f"Rasmni optimallashtirishda xato: {e}")
            # Agar Pillow ishlamasa, eski usulda o'qiymiz
            with open(target_image_path, "rb") as f:
                clean_base64 = base64.b64encode(f.read()).decode("utf-8")

        url = "https://api.segmind.com/v1/sdxl-img2img"
        payload = {
            "prompt": prompt,
            "negative_prompt": "ugly, bad resolution, deformed, completely different product, low quality, unnatural, artifacts",
            "image": clean_base64,
            "strength": 0.85,
            "guidance_scale": 9.0,
            "samples": 1,  # Segmindda sdxl-img2img odatda 1 ta rasm qaytaradi
            "scheduler": "UniPC",
            "num_inference_steps": 25,
            "base64": True
        }
        headers = {"x-api-key": self.api_key, "Content-Type": "application/json"}

        logger.info(f"Segmind xizmatiga so'rov yuborilmoqda: {url}")
        response = requests.post(url, json=payload, headers=headers, timeout=180)
        
        if response.status_code == 200:
            response_data = response.json()
            images = []
            
            if "image" in response_data:
                img_data = response_data["image"]
                if isinstance(img_data, list):
                    for img in img_data:
                        images.append({"mime_type": "image/jpeg", "base64": img})
                else:
                    images.append({"mime_type": "image/jpeg", "base64": img_data})
            else:
                raise Exception("Segmind API rasm qaytarmadi.")
                
            logger.info("Segmind rasm muvaffaqiyatli yaratildi.")
            return {"images": images[:output_count]}
        else:
            logger.error(f"Segmind Error: {response.text}")
            raise Exception(f"Segmind xatosi: {response.status_code} - {response.text}")
