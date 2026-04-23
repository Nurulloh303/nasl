from apps.ai_requests.prompt_data import QUALITY_SUFFIX

QUALITY_ENFORCEMENT = "CRITICAL QUALITY ENFORCEMENT: The final image MUST be of flawless, photorealistic, high-end commercial quality."
RATIO_STRICT_RULE = "CRITICAL: The output image MUST strictly fill the {ratio} frame."

STYLE_COPY_PROMPT = """You are a Master Visual Artist and E-commerce Designer.

TASK: Apply the visual style of the reference image to the uploaded product image.

{ratio_rule}

STRICT PRODUCT INTEGRITY RULES:
1. THE UPLOADED PRODUCT IS SACRED. Preserve its exact identity, shape, proportions, and important visual details.
2. ONLY change the background, lighting, and atmospheric effects to match the reference style.

TEXT & TYPOGRAPHY:
- Desired Headline: {smart_text}
- Key product characteristics: {characteristics}
- Language: Any text placed should be in {language}

ADDITIONAL STYLE NOTES: {custom_prompt}

{quality_rule}"""

def build_style_copy_prompt(data: dict) -> str:
    custom_prompt = data.get("custom_prompt", "").strip()
    ratio = data.get("ratio", "1:1")
    language = data.get("language", data.get("selectedInfoLang", "uz"))
    smart_text = data.get("smart_text", data.get("customSmartText", "")).strip()
    characteristics = data.get("characteristics", data.get("customCharacteristics", "")).strip()

    ratio_rule_filled = RATIO_STRICT_RULE.format(ratio=ratio)

    final_prompt = STYLE_COPY_PROMPT.format(
        ratio_rule=ratio_rule_filled,
        smart_text=smart_text if smart_text else "None",
        characteristics=characteristics if characteristics else "None",
        language=language,
        custom_prompt=custom_prompt if custom_prompt else "None",
        quality_rule=QUALITY_ENFORCEMENT
    )
    
    return final_prompt