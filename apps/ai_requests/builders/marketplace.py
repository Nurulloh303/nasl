from apps.ai_requests.prompt_data import MARKETPLACE_TEMPLATES, PHOTO_STYLES, QUALITY_SUFFIX

QUALITY_ENFORCEMENT = "CRITICAL QUALITY ENFORCEMENT: The final image MUST be of flawless, photorealistic, high-end commercial quality."
RATIO_STRICT_RULE = "CRITICAL: The output image MUST strictly fill the {ratio} frame."

MARKETPLACE_PACKAGE_PROMPT = """Act as a world-class E-commerce Graphic Designer and Art Director. Create a BESPOKE professional marketplace infographic package for this product.

{ratio_rule}

CREATIVE GUIDELINES:
1. DESIGN TYPE: This is NOT a template. It's a custom-made commercial design.
2. COMPOSITION: Create a dynamic and high-end advertising layout.
3. VISUAL STYLE: Use the {style} aesthetic as a foundation.
4. NO COLLAGE: This is ONE single, high-impact slide.
5. PRODUCT INTEGRITY: DO NOT ALTER THE PRODUCT'S FUNDAMENTAL FEATURES. It must be recognizable and 100% accurate.

PRODUCT INFORMATION:
- Product advantages: {description}
- Additional style request: {style_notes}
- Language: Use {language} language for visible copy.

{template_rule}
{quality_rule}"""

def build_marketplace_prompt(data: dict) -> str:
    template_id = data.get("template_id", "")
    ratio = data.get("ratio", "1:1")
    
    style_id = data.get("style_id", data.get("selectedPackageStyle", "minimalist"))
    style_prompt = data.get("style_prompt", PHOTO_STYLES.get(style_id, ""))
    
    product_description = data.get("product_description", data.get("packageProductDesc", "")).strip()
    style_description = data.get("style_description", data.get("packageStyleNotes", "")).strip()
    language = data.get("language", data.get("selectedInfoLang", "uz"))

    template = MARKETPLACE_TEMPLATES.get(template_id, {}) if template_id else {}
    template_rule = template.get("prompt", "")

    ratio_rule_filled = RATIO_STRICT_RULE.format(ratio=ratio)

    final_prompt = MARKETPLACE_PACKAGE_PROMPT.format(
        ratio_rule=ratio_rule_filled,
        style=style_prompt if style_prompt else "High-end commercial",
        description=product_description if product_description else "None",
        style_notes=style_description if style_description else "None",
        language=language,
        template_rule=template_rule,
        quality_rule=QUALITY_ENFORCEMENT
    )
    
    return final_prompt