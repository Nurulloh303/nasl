from apps.ai_requests.prompt_data import QUALITY_SUFFIX

def build_style_copy_prompt(data: dict) -> str:
    custom_prompt = data.get("custom_prompt", "").strip()
    parts = [
        "Apply the visual style of the reference image to the uploaded product image.",
        "Preserve the product identity, shape, proportions, and important visual details.",
    ]
    if custom_prompt:
        parts.append(f"Additional style notes: {custom_prompt}.")
    parts.append(QUALITY_SUFFIX)
    return " ".join(parts)
