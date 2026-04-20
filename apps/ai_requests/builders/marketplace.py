from apps.ai_requests.prompt_data import MARKETPLACE_TEMPLATES, PHOTO_STYLES, QUALITY_SUFFIX

def build_marketplace_prompt(data: dict) -> str:
    template_id = data.get("template_id", "")
    ratio = data.get("ratio", "")
    
    style_id = data.get("style_id", data.get("selectedPackageStyle", "minimalist"))
    style_prompt = data.get("style_prompt", PHOTO_STYLES.get(style_id, ""))
    
    product_description = data.get("product_description", data.get("packageProductDesc", "")).strip()
    style_description = data.get("style_description", data.get("packageStyleNotes", "")).strip()
    language = data.get("language", data.get("selectedInfoLang", "uz"))

    template = MARKETPLACE_TEMPLATES.get(template_id, {}) if template_id else {}

    parts = ["Create a professional marketplace infographic package for a product."]
    
    if ratio:
        parts.append(f"Aspect Ratio: {ratio}.")
    elif template:
        prompt_part = template.get("prompt", "")
        if prompt_part:
            parts.append(prompt_part)
            
    if style_prompt:
        parts.append(f"Visual style: {style_prompt}")
        
    if product_description:
        parts.append(f"Product information and advantages: {product_description}.")
    if style_description:
        parts.append(f"Additional style request: {style_description}.")
        
    parts.append(f"Use {language} language for visible copy.")
    parts.append("Make the output suitable for e-commerce marketplaces with clear selling points and clean composition.")
    parts.append(QUALITY_SUFFIX)
    return " ".join(part for part in parts if part)
