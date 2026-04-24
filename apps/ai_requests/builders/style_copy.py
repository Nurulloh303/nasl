from apps.ai_requests.prompt_data import QUALITY_SUFFIX

QUALITY_ENFORCEMENT = "CRITICAL QUALITY ENFORCEMENT: The final image MUST be of flawless, photorealistic, high-end commercial quality."
RATIO_STRICT_RULE = "STRICT ASPECT RATIO: {ratio}."

STYLE_COPY_PROMPT = """Task: Extract the visual language (composition, lighting, fonts, UI elements) from IMAGE 1 and apply it to the product in IMAGE 2.

{ratio_rule}

CRITICAL RULES:
1. DO NOT copy any brand names, logos, watermarks, store names, or promotional words (like "скидка", "акция", "sale", "discount", prices, percentages) from IMAGE 1. The final image must be unbranded or use the exact text provided in the Copy Strategy.
2. DO NOT change IMAGE 2 product pixels. Reposition and scale IMAGE 2 product creatively to fit the style of IMAGE 1.

COPY STRATEGY & TYPOGRAPHY:
- Language: {language}
- Text Strategy: {text_strategy}

ADDITIONAL STYLE NOTES: {custom_prompt}

{quality_rule}"""

def build_style_copy_prompt(data: dict) -> str:
    custom_prompt = data.get("custom_prompt", "").strip()
    ratio = data.get("ratio", "1:1")
    
    # Til sozlamasi
    raw_lang = data.get("language", data.get("selectedInfoLang", "uz"))
    language = "Uzbek (Latin script)" if raw_lang == "uz" else "Russian"
    
    # Matn strategiyasi
    smart_text = data.get("smart_text", data.get("customSmartText", "")).strip()
    characteristics = data.get("characteristics", data.get("customCharacteristics", "")).strip()
    
    if smart_text or characteristics:
        text_strategy = f'Headline: "{smart_text}", Features: "{characteristics}".'
    else:
        text_strategy = "AUTOMATIC: Analyze product and add professional copy."

    ratio_rule_filled = RATIO_STRICT_RULE.format(ratio=ratio)

    final_prompt = STYLE_COPY_PROMPT.format(
        ratio_rule=ratio_rule_filled,
        text_strategy=text_strategy,
        language=language,
        custom_prompt=custom_prompt if custom_prompt else "None",
        quality_rule=QUALITY_ENFORCEMENT
    )
    
    return final_prompt