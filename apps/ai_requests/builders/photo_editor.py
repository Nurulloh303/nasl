from apps.ai_requests.prompt_data import MARKETPLACE_TEMPLATES, PHOTO_STYLES, QUALITY_SUFFIX

QUALITY_ENFORCEMENT = "CRITICAL QUALITY ENFORCEMENT: Flawless, photorealistic, high-end commercial quality. NO distorted text, NO weird proportions."
RATIO_STRICT_RULE = "CRITICAL: The output image MUST strictly fill the {ratio} frame."

PHOTO_EDITOR_PROMPT = """You are an expert E-commerce Image Editor and Retoucher.

TASK: Enhance and place the uploaded product into a professional setting.

{ratio_rule}

STRICT PRODUCT INTEGRITY RULES:
1. THE PRODUCT MUST REMAIN EXACTLY THE SAME.
2. Do not distort the shape, change the text, or alter the color of the main product.

DIRECTION:
- Template Format: {template_name}
- Style: {style}
- Additional instructions: {custom_prompt}

{template_rule}
{quality_rule}"""

def build_photo_editor_prompt(data: dict) -> str:
    ratio = data.get("ratio", "1:1")
    template_id = data.get("template_id", "")
    style_id = data.get("style_id", "")
    style_prompt = data.get("style_prompt", data.get("promptSuffix", ""))
    custom_prompt = data.get("custom_prompt", data.get("customEditPrompt", "")).strip()

    template = MARKETPLACE_TEMPLATES.get(template_id, {})
    if not style_prompt and style_id:
        style_prompt = PHOTO_STYLES.get(style_id, "")

    ratio_rule_filled = RATIO_STRICT_RULE.format(ratio=ratio)

    final_prompt = PHOTO_EDITOR_PROMPT.format(
        ratio_rule=ratio_rule_filled,
        template_name=template.get('name', 'Standard'),
        style=style_prompt if style_prompt else "Clean studio",
        custom_prompt=custom_prompt if custom_prompt else "None",
        template_rule=template.get("prompt", ""),
        quality_rule=QUALITY_ENFORCEMENT
    )
    
    return final_prompt