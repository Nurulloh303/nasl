MODULE_DEFINITIONS = [
    {"id": "photo_editor", "label": "Foto Tahrir", "type": "image"},
    {"id": "fashion_ai", "label": "Fashion AI", "type": "image"},
    {"id": "infographic", "label": "Infografika", "type": "image"},
    {"id": "smart_text", "label": "Smart Matn", "type": "text"},
    {"id": "style_copy", "label": "Uslub Nusxalash", "type": "image"},
    {"id": "marketplace_pro", "label": "Marketplace Pro", "type": "image"},
    {"id": "fotosesiya_pro", "label": "Fotosessiya PRO", "type": "image"},
]

MARKETPLACE_TEMPLATES = {
    "uzum": {"name": "UZUM", "size": "1080x1440", "prompt": "Marketplace format for Uzum, size 1080x1440."},
    "wildberries": {"name": "WILDBERRIES", "size": "900x1200", "prompt": "Marketplace format for Wildberries, size 900x1200."},
    "yandex": {"name": "YANDEX MARKET", "size": "1080x1440", "prompt": "Marketplace format for Yandex Market, size 1080x1440."},
    "kvadrat": {"name": "KVADRAT", "size": "1080x1080", "prompt": "Square marketplace format, size 1080x1080."},
    "story": {"name": "STORY", "size": "1080x1920", "prompt": "Vertical story format, size 1080x1920."},
}

PHOTO_STYLES = {
    "minimalist": "Ultra-clean minimalist background, simple composition, soft shadows.",
    "bright": "Vibrant colorful composition, energetic lighting, attractive bright visual mood.",
    "premium": "Premium luxury dark setting with elegant gold accents and refined highlights.",
    "studio": "Professional studio photography setup, controlled light, soft grey backdrop.",
    "nature": "Natural setting with leaves, sunlight bokeh, organic atmosphere.",
    "neon": "Futuristic neon glow, cyberpunk accent lights, dark modern environment.",
    "vintage": "Vintage retro atmosphere, warm film tones, classic textured environment.",
    "loft": "Modern industrial loft interior, brick or concrete textures, natural window light.",
    "water": "Fresh water splash atmosphere, aqua tones, clean energetic composition.",
    "abstract": "Abstract 3D artistic composition, geometric forms, modern color transitions.",
    "home": "Cozy home environment, warm interior, realistic domestic lifestyle mood.",
    "tech": "Technology-focused futuristic environment, blue digital accents, clean technical feeling.",
}

INFOGRAPHIC_STYLES = {
    "info-clean": "Ultra-clean minimalist infographic, white background, soft shadows, clear typography.",
    "info-modern": "Modern energetic infographic, vibrant accent colors, dynamic geometric shapes, professional UI badges.",
    "info-premium": "Premium luxury infographic, deep dark background, gold and cyan highlights, elegant typography.",
    "info-tech": "Futuristic tech infographic, neon glowing lines, digital interfaces, high-tech HUD elements.",
    "info-nature": "Natural eco-friendly infographic, soft green and earth tones, leaf textures, organic shapes.",
    "info-exploded": "Detailed product analysis infographic, highlighting internal parts and mechanisms with callout lines.",
}

FASHION_GENDERS = {
    "female": "Use a female fashion model.",
    "male": "Use a male fashion model.",
    "none": "Do not use a model; present the item as a flat-lay or floating product.",
}

FASHION_POSES = {
    "front": "Front-facing standing pose.",
    "side": "Side-profile pose.",
    "dynamic": "Dynamic fashion movement pose.",
    "sitting": "Relaxed sitting pose.",
}

FASHION_STYLES = {
    "studio": "High-end studio lighting and catalog quality.",
    "street": "Street style urban editorial look.",
    "lookbook": "Clean lookbook and e-commerce catalog aesthetic.",
    "cinematic": "Cinematic dramatic lighting and fashion-ad atmosphere.",
}

FASHION_ENVS = {
    "minimal": "Minimal plain background.",
    "urban": "Modern urban city environment.",
    "interior": "Luxury modern interior environment.",
    "nature": "Natural outdoor environment.",
}

QUALITY_SUFFIX = "High resolution, realistic details, accurate proportions, commercial quality, no watermark, clean focus."
