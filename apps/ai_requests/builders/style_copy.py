from apps.ai_requests.prompt_data import QUALITY_SUFFIX

def build_style_copy_prompt(data: dict) -> str:
    custom_prompt = data.get("custom_prompt", "").strip()
    ratio = data.get("ratio", "")
    language = data.get("language", data.get("selectedInfoLang", "uz"))
    smart_text = data.get("smart_text", data.get("customSmartText", "")).strip()
    characteristics = data.get("characteristics", data.get("customCharacteristics", "")).strip()

    parts = [
        "Apply the visual style of the reference image to the uploaded product image.",
        "Preserve the product identity, shape, proportions, and important visual details.",
    ]
    if ratio:
        parts.append(f"Aspect Ratio: {ratio}.")
    if smart_text:
        parts.append(f"Desired Headline: {smart_text}.")
    if characteristics:
        parts.append(f"Key product characteristics: {characteristics}.")
    if language != "uz":
        parts.append(f"Any text placed should be in {language}.")
        
    if custom_prompt:
        parts.append(f"Additional style notes: {custom_prompt}.")
    parts.append(QUALITY_SUFFIX)
    return " ".join(parts)
