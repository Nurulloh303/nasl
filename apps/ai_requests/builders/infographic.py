from apps.ai_requests.prompt_data import INFOGRAPHIC_STYLES, QUALITY_SUFFIX

def build_infographic_prompt(data: dict) -> str:
    style_id = data.get("style_id", "")
    style_prompt = data.get("style_prompt", data.get("promptSuffix", ""))
    
    if not style_prompt and style_id:
        style_prompt = INFOGRAPHIC_STYLES.get(style_id, "")

    title_text = data.get("title_text", data.get("customSmartText", "")).strip()
    characteristics = data.get("characteristics", data.get("customCharacteristics", "")).strip()
    custom_prompt = data.get("custom_prompt", data.get("customInfoPrompt", "")).strip()
    language = data.get("language", data.get("selectedInfoLang", "uz"))
    ratio = data.get("ratio", "")
    density = data.get("density", data.get("selectedDensity", ""))

    parts = ["Create a product infographic based on the uploaded image."]
    if ratio:
        parts.append(f"Aspect Ratio: {ratio}.")
    if style_prompt:
        parts.append(style_prompt)
    if title_text:
        parts.append(f"Headline: {title_text}.")
    if characteristics:
        parts.append(f"Key product characteristics: {characteristics}.")
    if custom_prompt:
        parts.append(f"Additional instructions: {custom_prompt}.")
    if density:
        parts.append(f"Desired detail density: {density} text.")
        
    parts.append(f"All visible text must be in {language}.")
    parts.append("Strong visual hierarchy, readable labels, clear callouts, product-centered composition.")
    parts.append(QUALITY_SUFFIX)
    return " ".join(part for part in parts if part)
