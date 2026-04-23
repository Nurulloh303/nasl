QUALITY_ENFORCEMENT = "CRITICAL QUALITY ENFORCEMENT: The final image MUST be of flawless, photorealistic, high-end commercial quality. Typography must be perfectly legible and aesthetic."
RATIO_STRICT_RULE = "CRITICAL: The output image MUST strictly fill the {ratio} frame."

SMART_TEXT_PROMPT = """You are a world-class graphic designer specializing in commercial product cards. 

{ratio_rule}

STRICT RULE: THE PRODUCT IMAGE AND BACKGROUND MUST NOT BE CHANGED OR DISTORTED. 
TASK: Add professional, aesthetic typography to the image seamlessly.

TEXT CONTENT:
- Product title: {title}
- Product details: {description}

TYPOGRAPHY RULES:
- Language: {language}
- Tone: {tone}
- Style: Keep it persuasive, concise, and suitable for marketplaces.

{quality_rule}"""

def build_smart_text_prompt(data: dict) -> str:
    product_description = data.get("product_description", data.get("customCharacteristics", "")).strip()
    language = data.get("language", data.get("selectedInfoLang", "uz"))
    tone = data.get("tone", "marketing")
    title = data.get("title", data.get("customSmartText", "")).strip()
    ratio = data.get("ratio", "1:1")

    ratio_rule_filled = RATIO_STRICT_RULE.format(ratio=ratio)

    final_prompt = SMART_TEXT_PROMPT.format(
        ratio_rule=ratio_rule_filled,
        title=title if title else "None",
        description=product_description if product_description else "None",
        language=language,
        tone=tone,
        quality_rule=QUALITY_ENFORCEMENT
    )
    
    return final_prompt