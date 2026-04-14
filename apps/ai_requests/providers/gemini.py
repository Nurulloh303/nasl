import base64
import logging
import mimetypes
from pathlib import Path

from django.conf import settings

try:
    from google import genai
except Exception:  # pragma: no cover
    genai = None

from .base import BaseAIProvider

logger = logging.getLogger(__name__)

class GeminiProvider(BaseAIProvider):
    name = "gemini"

    def __init__(self):
        if not settings.GEMINI_API_KEY:
            raise RuntimeError("GEMINI_API_KEY topilmadi.")
        if genai is None:
            raise RuntimeError("google-genai kutubxonasi o'rnatilmagan.")
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)

    def generate_text(self, prompt: str, data: dict):
        try:
            response = self.client.models.generate_content(
                model=settings.GEMINI_TEXT_MODEL,
                contents=prompt,
            )
            text = getattr(response, "text", "") or ""
            logger.info(f"Gemini text generation successful for model {settings.GEMINI_TEXT_MODEL}")
            return {"texts": [text]}
        except Exception as e:
            logger.error(f"Gemini text generation failed: {str(e)}")
            raise

    def generate_images(self, prompt: str, image_paths: list[str], output_count: int = 1):
        try:
            parts = []
            for image_path in image_paths:
                path = Path(image_path)
                mime_type = mimetypes.guess_type(path.name)[0] or "image/jpeg"
                with open(path, "rb") as f:
                    encoded = base64.b64encode(f.read()).decode("utf-8")
                parts.append({
                    "inline_data": {
                        "mime_type": mime_type,
                        "data": encoded,
                    }
                })
            parts.append({"text": prompt})

            response = self.client.models.generate_content(
                model=settings.GEMINI_IMAGE_MODEL,
                contents=[{"parts": parts}],
            )

            images = []
            candidates = getattr(response, "candidates", []) or []
            for candidate in candidates:
                content = getattr(candidate, "content", None)
                if not content:
                    continue
                for part in getattr(content, "parts", []) or []:
                    inline_data = getattr(part, "inline_data", None) or getattr(part, "inlineData", None)
                    if inline_data:
                        mime_type = getattr(inline_data, "mime_type", None) or getattr(inline_data, "mimeType", "image/png")
                        data = getattr(inline_data, "data", None)
                        if data:
                            images.append({"mime_type": mime_type, "base64": data})

            if not images:
                logger.warning("Gemini did not return any images. Check prompt or model.")
                raise RuntimeError("Gemini rasm qaytarmadi. Promptni tekshiring yoki boshqa modeldan foydalaning.")
            logger.info(f"Gemini image generation successful, generated {len(images)} images")
            return {"images": images[:output_count]}
        except Exception as e:
            logger.error(f"Gemini image generation failed: {str(e)}")
            raise
