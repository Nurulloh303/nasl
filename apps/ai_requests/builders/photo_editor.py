from apps.ai_requests.prompt_data import MARKETPLACE_TEMPLATES, PHOTO_STYLES, QUALITY_SUFFIX

def build_photo_editor_prompt(data: dict) -> str:
    template_id = data.get("template_id", "uzum")
    style_id = data.get("style_id", "studio")
    custom_prompt = data.get("custom_prompt", "").strip()

    template = MARKETPLACE_TEMPLATES.get(template_id, {})
    style_prompt = PHOTO_STYLES.get(style_id, "")

    parts = [
        f"Professional product photo for {template.get('name', 'marketplace')}.",
        template.get("prompt", ""),
        f"Style: {style_prompt}",
    ]
    if custom_prompt:
        parts.append(f"Additional instructions: {custom_prompt}.")
    parts.append(QUALITY_SUFFIX)
    return " ".join(part for part in parts if part)
