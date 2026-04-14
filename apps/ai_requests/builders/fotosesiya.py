from apps.ai_requests.prompt_data import QUALITY_SUFFIX

def build_fotosesiya_prompt(data: dict) -> str:
    custom_prompt = data.get("custom_prompt", "").strip()
    count = int(data.get("image_count", 2))
    parts = [
        f"Create {count} professional photoshoot scenes for the uploaded product.",
        "Each generated image should have a unique commercial composition and advertising-ready presentation.",
    ]
    if custom_prompt:
        parts.append(f"Photoshoot direction: {custom_prompt}.")
    parts.append("Use premium lighting, realistic shadows, and strong product focus.")
    parts.append(QUALITY_SUFFIX)
    return " ".join(parts)
