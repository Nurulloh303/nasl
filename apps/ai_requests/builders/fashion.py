from apps.ai_requests.prompt_data import (
    FASHION_ENVS,
    FASHION_GENDERS,
    FASHION_POSES,
    FASHION_STYLES,
    QUALITY_SUFFIX,
)

def build_fashion_prompt(data: dict) -> str:
    custom_prompt = data.get("custom_prompt", "").strip()
    parts = [
        "Create a professional fashion image from the uploaded clothing or footwear photo.",
        FASHION_GENDERS.get(data.get("gender_id", "female"), ""),
        FASHION_POSES.get(data.get("pose_id", "front"), ""),
        FASHION_STYLES.get(data.get("style_id", "studio"), ""),
        FASHION_ENVS.get(data.get("env_id", "minimal"), ""),
    ]
    if custom_prompt:
        parts.append(f"Extra direction: {custom_prompt}.")
    parts.append("Preserve item details, fabric texture, logo placement, and realistic fit.")
    parts.append(QUALITY_SUFFIX)
    return " ".join(part for part in parts if part)
