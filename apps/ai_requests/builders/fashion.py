from apps.ai_requests.prompt_data import (
    FASHION_ENVS,
    FASHION_GENDERS,
    FASHION_POSES,
    FASHION_STYLES,
    QUALITY_SUFFIX,
)

def build_fashion_prompt(data: dict) -> str:
    custom_prompt = data.get("custom_prompt", data.get("customFashionPrompt", "")).strip()
    
    gender_id = data.get("gender_id", data.get("fashionGender", "female"))
    gender_prompt = FASHION_GENDERS.get(gender_id, gender_id)
    
    pose_prompt = data.get("pose_prompt", FASHION_POSES.get(data.get("pose_id", ""), ""))
    style_prompt = data.get("style_prompt", FASHION_STYLES.get(data.get("style_id", ""), ""))
    env_prompt = data.get("env_prompt", FASHION_ENVS.get(data.get("env_id", ""), ""))
    
    ratio = data.get("ratio", "")

    parts = [
        "Create a professional fashion image from the uploaded clothing or footwear photo."
    ]
    if gender_prompt: parts.append(gender_prompt)
    if pose_prompt: parts.append(pose_prompt)
    if style_prompt: parts.append(style_prompt)
    if env_prompt: parts.append(env_prompt)
    if ratio: parts.append(f"Aspect Ratio: {ratio}.")

    if custom_prompt:
        parts.append(f"Extra direction: {custom_prompt}.")
        
    parts.append("Preserve item details, fabric texture, logo placement, and realistic fit.")
    parts.append(QUALITY_SUFFIX)
    return " ".join(part for part in parts if part)
