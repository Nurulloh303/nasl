def build_smart_text_prompt(data: dict) -> str:
    product_description = data.get("product_description", data.get("customCharacteristics", "")).strip()
    language = data.get("language", data.get("selectedInfoLang", "uz"))
    tone = data.get("tone", "marketing")
    output_type = data.get("output_type", "product_description")
    title = data.get("title", data.get("customSmartText", "")).strip()
    ratio = data.get("ratio", "")

    parts = [
        f"Write {output_type} text for an e-commerce product.",
        f"Language: {language}.",
        f"Tone: {tone}.",
    ]
    if title:
        parts.append(f"Product title: {title}.")
    if product_description:
        parts.append(f"Product details: {product_description}.")
    if ratio:
        parts.append(f"Rendered image context aspect ratio: {ratio}.")
        
    parts.append("Keep it persuasive, concise, and suitable for marketplaces like Uzum and Wildberries.")
    return " ".join(parts)
