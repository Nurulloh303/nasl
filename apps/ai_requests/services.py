import base64
import logging
import time

from django.conf import settings
from django.core.files.base import ContentFile
from django.utils import timezone

from .models import GenerationAsset, GenerationRequest, UploadedSourceImage, UsageLog
from .prompt_dispatcher import build_prompt
from .providers.gemini import GeminiProvider
from .providers.mock import MockProvider

logger = logging.getLogger(__name__)

IMAGE_MODULES = {"photo_editor", "fashion_ai", "infographic", "style_copy", "marketplace_pro", "fotosesiya_pro"}
TEXT_MODULES = {"smart_text"}


def get_provider():
    provider_name = settings.DEFAULT_GENERATION_PROVIDER
    if provider_name == "gemini":
        try:
            return GeminiProvider()
        except Exception:
            return MockProvider()
    return MockProvider()


def save_uploaded_files(gen_request: GenerationRequest, files):
    allowed_types = {"image/jpeg", "image/png", "image/webp"}
    max_size = 50 * 1024 * 1024
    count = 0
    for idx, file in enumerate(files):
        if hasattr(file, "content_type") and file.content_type not in allowed_types:
            logger.warning("Invalid file type for request %s: %s", gen_request.id, file.content_type)
            continue
        if file.size > max_size:
            logger.warning("File too large for request %s: %s bytes", gen_request.id, file.size)
            continue
        uploaded = UploadedSourceImage(
            request=gen_request,
            order=idx,
            original_name=file.name,
            mime_type=getattr(file, "content_type", ""),
            size_bytes=file.size,
        )
        uploaded.image.save(file.name, file, save=True)
        count += 1
    gen_request.input_count = count
    gen_request.save(update_fields=["input_count"])
    return count


def _store_image_asset(gen_request: GenerationRequest, payload: dict, order: int):
    raw = base64.b64decode(payload["base64"])
    ext = payload.get("mime_type", "image/png").split("/")[-1]
    name = f"{gen_request.id}_{order}.{ext}"
    asset = GenerationAsset(
        request=gen_request,
        kind=GenerationAsset.KIND_IMAGE,
        order=order,
        mime_type=payload.get("mime_type", "image/png"),
    )
    asset.file.save(name, ContentFile(raw), save=True)
    return asset


def _store_text_asset(gen_request: GenerationRequest, text: str, order: int = 0):
    return GenerationAsset.objects.create(
        request=gen_request,
        kind=GenerationAsset.KIND_TEXT,
        text=text,
        order=order,
        mime_type="text/plain",
    )


def _refund_if_needed(gen_request: GenerationRequest):
    if gen_request.credits_charged > 0 and not gen_request.credits_refunded:
        gen_request.user.profile.refund_generation_tokens(gen_request.credits_charged)
        gen_request.credits_refunded = True
        gen_request.save(update_fields=["credits_refunded"])


def execute_generation(gen_request: GenerationRequest):
    started = time.perf_counter()
    gen_request.status = GenerationRequest.STATUS_PROCESSING
    gen_request.started_at = timezone.now()
    gen_request.save(update_fields=["status", "started_at"])

    provider = get_provider()
    prompt = gen_request.prompt
    data = gen_request.payload
    image_paths = [src.image.path for src in gen_request.source_images.all()]
    output_count = int(data.get("image_count", 1))

    try:
        if gen_request.module in TEXT_MODULES:
            result = provider.generate_text(prompt, data)
            texts = result.get("texts", [])
            for idx, text in enumerate(texts):
                _store_text_asset(gen_request, text, idx)
            gen_request.output_count = len(texts) or 1
        else:
            result = provider.generate_images(prompt, image_paths=image_paths, output_count=output_count)
            images = result.get("images", [])
            for idx, image_payload in enumerate(images):
                _store_image_asset(gen_request, image_payload, idx)
            gen_request.output_count = len(images) or 1

        gen_request.status = GenerationRequest.STATUS_COMPLETED
        gen_request.completed_at = timezone.now()
        gen_request.error_message = ""
        gen_request.save(update_fields=["status", "completed_at", "error_message", "output_count"])
        UsageLog.objects.update_or_create(
            request=gen_request,
            defaults={
                "provider": provider.name,
                "success": True,
                "credits_used": gen_request.credits_charged or (0 if gen_request.used_free_generation else max(1, settings.GENERATION_TOKEN_COST)),
                "response_time_ms": int((time.perf_counter() - started) * 1000),
            },
        )
    except Exception as exc:
        logger.exception("Generation failed for request %s: %s", gen_request.id, exc)
        _refund_if_needed(gen_request)
        gen_request.status = GenerationRequest.STATUS_FAILED
        gen_request.error_message = str(exc)
        gen_request.completed_at = timezone.now()
        gen_request.save(update_fields=["status", "error_message", "completed_at"])
        UsageLog.objects.update_or_create(
            request=gen_request,
            defaults={
                "provider": provider.name,
                "success": False,
                "credits_used": 0,
                "response_time_ms": int((time.perf_counter() - started) * 1000),
            },
        )
        raise


def create_generation_request(*, user, module: str, data: dict, files, credits_charged: int = 0, used_free_generation: bool = False):
    prompt = build_prompt(module, data)
    gen_request = GenerationRequest.objects.create(
        user=user,
        module=module,
        provider=settings.DEFAULT_GENERATION_PROVIDER,
        prompt=prompt,
        payload=data,
        output_count=int(data.get("image_count", 1) if module in IMAGE_MODULES else 1),
        credits_charged=credits_charged,
        used_free_generation=used_free_generation,
    )
    if files:
        save_uploaded_files(gen_request, files)
    return gen_request
