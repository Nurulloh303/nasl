from apps.ai_requests.prompt_data import QUALITY_SUFFIX

QUALITY_ENFORCEMENT = "CRITICAL QUALITY ENFORCEMENT: The final image MUST be of flawless, photorealistic, high-end commercial quality. Absolutely NO artifacts, NO distorted text, NO weird proportions, and NO hallucinations. Ensure perfect lighting, sharp details, and a premium aesthetic."
RATIO_STRICT_RULE = "CRITICAL: The output image MUST strictly fill the {ratio} frame. No margins, no letterboxing."

FOTOSESIYA_PROMPT = """You are a High-End Commercial Product Photographer.

TASK: Create {count} professional photoshoot scenes for the uploaded product. Each generated image should have a unique commercial composition and advertising-ready presentation.

{ratio_rule}

STRICT PRODUCT INTEGRITY RULES:
1. DO NOT CHANGE THE PRODUCT ITSELF.
2. Preserve the exact shape, material, color, text, and brand details of the original item.
3. Only modify the environment, background, and lighting.

CREATIVE DIRECTION:
- Style: {style}
- Photoshoot direction: {custom_prompt}

Use premium lighting, realistic shadows, and strong product focus.
{quality_rule}"""

def build_fotosesiya_prompt(data: dict) -> str:
    custom_prompt = data.get("custom_prompt", data.get("customFotosesiyaPrompt", "")).strip()
    count = int(data.get("image_count", data.get("fotosesiyaCount", 2)))
    ratio = data.get("ratio", "1:1")
    style_prompt = data.get("style_prompt", data.get("promptSuffix", ""))

    ratio_rule_filled = RATIO_STRICT_RULE.format(ratio=ratio)

    final_prompt = FOTOSESIYA_PROMPT.format(
        count=count,
        ratio_rule=ratio_rule_filled,
        style=style_prompt if style_prompt else "Professional studio lighting",
        custom_prompt=custom_prompt if custom_prompt else "None",
        quality_rule=QUALITY_ENFORCEMENT
    )
    
    return final_prompt