def build_smart_text_prompt(data: dict) -> str:
    product_description = data.get("product_description", "").strip()
    language = data.get("language", "uz")
    tone = data.get("tone", "marketing")
    output_type = data.get("output_type", "product_description")
    title = data.get("title", "").strip()

    parts = [
        f"Write {output_type} text for an e-commerce product.",
        f"Language: {language}.",
        f"Tone: {tone}.",
    ]
    if title:
        parts.append(f"Product title: {title}.")
    if product_description:
        parts.append(f"Product details: {product_description}.")
    parts.append("Keep it persuasive, concise, and suitable for marketplaces like Uzum and Wildberries.")
    return " ".join(parts)
