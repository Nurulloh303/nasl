from apps.ai_requests.prompt_data import MARKETPLACE_TEMPLATES, PHOTO_STYLES, QUALITY_SUFFIX

def build_photo_editor_prompt(data: dict) -> str:
    ratio = data.get("ratio", "")
    template_id = data.get("template_id", "")
    style_id = data.get("style_id", "")
    style_prompt = data.get("style_prompt", data.get("promptSuffix", ""))
    custom_prompt = data.get("custom_prompt", data.get("customEditPrompt", "")).strip()

    template = MARKETPLACE_TEMPLATES.get(template_id, {})
    if not style_prompt and style_id:
        style_prompt = PHOTO_STYLES.get(style_id, "")

    parts = ["Professional product photo."]
    
    if ratio:
        parts.append(f"Aspect Ratio: {ratio}.")
    elif template:
        parts.append(f"Template format: {template.get('name', 'marketplace')}.")
        prompt_part = template.get("prompt", "")
        if prompt_part:
            parts.append(prompt_part)
            
    if style_prompt:
        parts.append(f"Style: {style_prompt}")

    if custom_prompt:
        parts.append(f"Additional instructions: {custom_prompt}.")
        
    parts.append(QUALITY_SUFFIX)
    return " ".join(part for part in parts if part)
