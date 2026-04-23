from apps.ai_requests.prompt_data import INFOGRAPHIC_STYLES, QUALITY_SUFFIX

QUALITY_ENFORCEMENT = "CRITICAL QUALITY ENFORCEMENT: The final image MUST be of flawless, photorealistic, high-end commercial quality. Absolutely NO artifacts, NO distorted text, NO weird proportions, and NO hallucinations."
RATIO_STRICT_RULE = "CRITICAL: The output image MUST strictly fill the {ratio} frame."

INFOGRAPHIC_PROMPT = """Act as a High-End Advertising Art Director for Marketplaces. Your goal is to create a dynamic and creative product card.

{ratio_rule}

CREATIVE MANDATE:
1. DYNAMIC LAYOUT: Do not just center the product. Place it strategically to create a premium feel.
2. BESPOKE BACKGROUND: Design a custom environment based on the product's use-case.
3. TYPOGRAPHY: Use professional, high-impact marketplace fonts.
4. PRODUCT PIXELS: Keep the product's original details 100% accurate. DO NOT MODIFY THE UPLOADED PRODUCT ITSELF.

TEXT & DETAILS:
- Headline: {title_text}
- Key product characteristics: {characteristics}
- Density: {density} text
- Language: All visible text must be in {language}

STYLE & INSTRUCTIONS:
- Style: {style}
- Additional instructions: {custom_prompt}

{quality_rule}"""

def build_infographic_prompt(data: dict) -> str:
    style_id = data.get("style_id", "")
    style_prompt = data.get("style_prompt", data.get("promptSuffix", ""))
    
    if not style_prompt and style_id:
        style_prompt = INFOGRAPHIC_STYLES.get(style_id, "")

    title_text = data.get("title_text", data.get("customSmartText", "")).strip()
    characteristics = data.get("characteristics", data.get("customCharacteristics", "")).strip()
    custom_prompt = data.get("custom_prompt", data.get("customInfoPrompt", "")).strip()
    language = data.get("language", data.get("selectedInfoLang", "uz"))
    ratio = data.get("ratio", "1:1")
    density = data.get("density", data.get("selectedDensity", "balanced"))

    ratio_rule_filled = RATIO_STRICT_RULE.format(ratio=ratio)

    final_prompt = INFOGRAPHIC_PROMPT.format(
        ratio_rule=ratio_rule_filled,
        title_text=title_text if title_text else "None",
        characteristics=characteristics if characteristics else "None",
        density=density,
        language=language,
        style=style_prompt if style_prompt else "Modern marketplace style",
        custom_prompt=custom_prompt if custom_prompt else "None",
        quality_rule=QUALITY_ENFORCEMENT
    )
    
    return final_prompt