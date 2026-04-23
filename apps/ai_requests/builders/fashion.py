from apps.ai_requests.prompt_data import (
    FASHION_ENVS,
    FASHION_GENDERS,
    FASHION_POSES,
    FASHION_STYLES,
)

# DO'STINGIZ YOZGAN QOIDALAR (Constants):
QUALITY_ENFORCEMENT = "CRITICAL QUALITY ENFORCEMENT: The final image MUST be of flawless, photorealistic, high-end commercial quality. Absolutely NO artifacts, NO distorted text, NO weird proportions, and NO hallucinations. Ensure perfect lighting, sharp details, and a premium aesthetic."

RATIO_STRICT_RULE = "CRITICAL: The output image MUST strictly fill the {ratio} frame. No margins, no letterboxing. The composition must be native to the {ratio} dimensions."

# DO'STINGIZNING ASOSIY FASHION PROMPTI:
FASHION_AI_PROMPT = """You are a professional fashion photographer and AI stylist. 

TASK: Take the product from the image (clothing, shoes, or accessory) and place it realistically on a high-quality human model or professional flat-lay arrangement.

{ratio_rule}

STRICT PRODUCT INTEGRITY RULES:
1. DO NOT CHANGE THE PRODUCT ITSELF.
2. Maintain exactly the same color, texture, prints, logos, and structure.

ENVIRONMENT & MODEL RULES:
- If a model is chosen: Place the product on a {gender} model.
- Pose: Use a {pose} stance.
- Style: Follow a {style} photography aesthetic.
- Background: Use a {env} location.

USER SPECIFIC REQUESTS: {custom_prompt}

{quality_rule}"""

def build_fashion_prompt(data: dict) -> str:
    # 1. Foydalanuvchi tanlagan ma'lumotlarni tutib olamiz
    custom_prompt = data.get("custom_prompt", data.get("customFashionPrompt", "")).strip()
    
    gender_id = data.get("gender_id", data.get("fashionGender", "female"))
    gender_prompt = FASHION_GENDERS.get(gender_id, gender_id)
    
    pose_prompt = data.get("pose_prompt", FASHION_POSES.get(data.get("pose_id", ""), ""))
    style_prompt = data.get("style_prompt", FASHION_STYLES.get(data.get("style_id", ""), ""))
    env_prompt = data.get("env_prompt", FASHION_ENVS.get(data.get("env_id", ""), ""))
    
    ratio = data.get("ratio", "1:1")
    
    # 2. Proportion (Ratio) qoidasiga razmerni joylaymiz
    ratio_rule_filled = RATIO_STRICT_RULE.format(ratio=ratio)

    # 3. Do'stingizning shabloniga hamma ma'lumotlarni yopishtiramiz
    final_prompt = FASHION_AI_PROMPT.format(
        ratio_rule=ratio_rule_filled,
        gender=gender_prompt if gender_prompt else "standard",
        pose=pose_prompt if pose_prompt else "natural",
        style=style_prompt if style_prompt else "professional",
        env=env_prompt if env_prompt else "studio",
        custom_prompt=custom_prompt if custom_prompt else "None",
        quality_rule=QUALITY_ENFORCEMENT
    )
    
    return final_prompt