from apps.ai_requests.prompt_data import MARKETPLACE_TEMPLATES, PHOTO_STYLES, QUALITY_SUFFIX

QUALITY_ENFORCEMENT = "CRITICAL QUALITY ENFORCEMENT: Flawless, photorealistic, high-end commercial quality. NO distorted text."
RATIO_STRICT_RULE = "STRICT ASPECT RATIO: {ratio}."

PHOTO_EDITOR_PROMPT = """You are an expert E-commerce Image Editor and Retoucher.

TASK: Professional background replacement.
{ratio_rule}

STRICT PRODUCT INTEGRITY RULES:
1. CRITICAL: Do NOT distort the product! The main product MUST remain exactly the same.
2. Do not change the text, shape, or color of the uploaded item.

DIRECTION:
- Template Format: {template_name}
- Style: {style}
- User Note: {custom_prompt}

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