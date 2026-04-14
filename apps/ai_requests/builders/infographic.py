from apps.ai_requests.prompt_data import INFOGRAPHIC_STYLES, QUALITY_SUFFIX

def build_infographic_prompt(data: dict) -> str:
    style_id = data.get("style_id", "info-clean")
    title_text = data.get("title_text", "").strip()
    characteristics = data.get("characteristics", "").strip()
    custom_prompt = data.get("custom_prompt", "").strip()
    language = data.get("language", "uz")

    parts = [
        "Create a product infographic based on the uploaded image.",
        INFOGRAPHIC_STYLES.get(style_id, ""),
    ]
    if title_text:
        parts.append(f"Headline: {title_text}.")
    if characteristics:
        parts.append(f"Key product characteristics: {characteristics}.")
    if custom_prompt:
        parts.append(f"Additional instructions: {custom_prompt}.")
    parts.append(f"All visible text must be in {language}.")
    parts.append("Strong visual hierarchy, readable labels, clear callouts, product-centered composition.")
    parts.append(QUALITY_SUFFIX)
    return " ".join(part for part in parts if part)
