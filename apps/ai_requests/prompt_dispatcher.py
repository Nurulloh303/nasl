from apps.ai_requests.builders.fashion import build_fashion_prompt
from apps.ai_requests.builders.fotosesiya import build_fotosesiya_prompt
from apps.ai_requests.builders.infographic import build_infographic_prompt
from apps.ai_requests.builders.marketplace import build_marketplace_prompt
from apps.ai_requests.builders.photo_editor import build_photo_editor_prompt
from apps.ai_requests.builders.smart_text import build_smart_text_prompt
from apps.ai_requests.builders.style_copy import build_style_copy_prompt

def build_prompt(module_name: str, data: dict) -> str:
    builders = {
        "photo_editor": build_photo_editor_prompt,
        "fashion_ai": build_fashion_prompt,
        "infographic": build_infographic_prompt,
        "smart_text": build_smart_text_prompt,
        "style_copy": build_style_copy_prompt,
        "marketplace_pro": build_marketplace_prompt,
        "fotosesiya_pro": build_fotosesiya_prompt,
    }
    if module_name not in builders:
        raise ValueError(f"Invalid module name: {module_name}")
    return builders[module_name](data)
