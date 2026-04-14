import uuid

from django.conf import settings
from django.db import models


class GenerationRequest(models.Model):
    STATUS_PENDING = "pending"
    STATUS_PROCESSING = "processing"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_PROCESSING, "Processing"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_FAILED, "Failed"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="generation_requests")
    module = models.CharField(max_length=64)
    provider = models.CharField(max_length=50, default="gemini")
    prompt = models.TextField()
    payload = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    error_message = models.TextField(blank=True)
    input_count = models.PositiveIntegerField(default=0)
    output_count = models.PositiveIntegerField(default=1)
    credits_charged = models.PositiveIntegerField(default=0)
    used_free_generation = models.BooleanField(default=False)
    credits_refunded = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["status"]),
            models.Index(fields=["-created_at"]),
        ]

    def __str__(self):
        return f"{self.module} - {self.user.username} - {self.status}"


class GenerationAsset(models.Model):
    KIND_IMAGE = "image"
    KIND_TEXT = "text"
    KIND_CHOICES = [
        (KIND_IMAGE, "Image"),
        (KIND_TEXT, "Text"),
    ]

    request = models.ForeignKey(GenerationRequest, on_delete=models.CASCADE, related_name="assets")
    kind = models.CharField(max_length=20, choices=KIND_CHOICES)
    file = models.ImageField(upload_to="generated/", blank=True, null=True)
    text = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)
    mime_type = models.CharField(max_length=100, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ("order",)


class UploadedSourceImage(models.Model):
    request = models.ForeignKey(GenerationRequest, on_delete=models.CASCADE, related_name="source_images")
    image = models.ImageField(upload_to="uploads/")
    order = models.PositiveIntegerField(default=0)
    original_name = models.CharField(max_length=255, blank=True)
    mime_type = models.CharField(max_length=100, blank=True)
    size_bytes = models.PositiveBigIntegerField(default=0)


class UsageLog(models.Model):
    request = models.OneToOneField(GenerationRequest, on_delete=models.CASCADE, related_name="usage_log")
    provider = models.CharField(max_length=50)
    success = models.BooleanField(default=False)
    credits_used = models.PositiveIntegerField(default=0)
    estimated_cost = models.DecimalField(max_digits=8, decimal_places=3, default=0)
    response_time_ms = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
