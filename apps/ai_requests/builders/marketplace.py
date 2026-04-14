from apps.ai_requests.prompt_data import MARKETPLACE_TEMPLATES, PHOTO_STYLES, QUALITY_SUFFIX

def build_marketplace_prompt(data: dict) -> str:
    template_id = data.get("template_id", "uzum")
    style_id = data.get("style_id", "minimalist")
    product_description = data.get("product_description", "").strip()
    style_description = data.get("style_description", "").strip()
    language = data.get("language", "uz")

    template = MARKETPLACE_TEMPLATES.get(template_id, {})
    style_prompt = PHOTO_STYLES.get(style_id, "")

    parts = [
        "Create a professional marketplace infographic package for a product.",
        template.get("prompt", ""),
        f"Visual style: {style_prompt}",
    ]
    if product_description:
        parts.append(f"Product information and advantages: {product_description}.")
    if style_description:
        parts.append(f"Additional style request: {style_description}.")
    parts.append(f"Use {language} language for visible copy.")
    parts.append("Make the output suitable for e-commerce marketplaces with clear selling points and clean composition.")
    parts.append(QUALITY_SUFFIX)
    return " ".join(part for part in parts if part)
