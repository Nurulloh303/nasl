import base64

from .base import BaseAIProvider

ONE_PIXEL_PNG = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO1dR7kAAAAASUVORK5CYII="

class MockProvider(BaseAIProvider):
    name = "mock"

    def generate_text(self, prompt: str, data: dict):
        return {"texts": [f"[MOCK TEXT]\n{prompt}"]}

    def generate_images(self, prompt: str, image_paths: list[str], output_count: int = 1):
        return {
            "images": [
                {"mime_type": "image/png", "base64": ONE_PIXEL_PNG}
                for _ in range(max(1, output_count))
            ]
        }
