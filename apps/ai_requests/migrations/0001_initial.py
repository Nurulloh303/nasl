import uuid
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="GenerationRequest",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("module", models.CharField(max_length=64)),
                ("provider", models.CharField(default="gemini", max_length=50)),
                ("prompt", models.TextField()),
                ("payload", models.JSONField(blank=True, default=dict)),
                ("status", models.CharField(choices=[("pending", "Pending"), ("processing", "Processing"), ("completed", "Completed"), ("failed", "Failed")], default="pending", max_length=20)),
                ("error_message", models.TextField(blank=True)),
                ("input_count", models.PositiveIntegerField(default=0)),
                ("output_count", models.PositiveIntegerField(default=1)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("started_at", models.DateTimeField(blank=True, null=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="generation_requests", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ("-created_at",)},
        ),
        migrations.CreateModel(
            name="GenerationAsset",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("kind", models.CharField(choices=[("image", "Image"), ("text", "Text")], max_length=20)),
                ("file", models.ImageField(blank=True, null=True, upload_to="generated/")),
                ("text", models.TextField(blank=True)),
                ("order", models.PositiveIntegerField(default=0)),
                ("mime_type", models.CharField(blank=True, max_length=100)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("request", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="assets", to="ai_requests.generationrequest")),
            ],
            options={"ordering": ("order",)},
        ),
        migrations.CreateModel(
            name="UploadedSourceImage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("image", models.ImageField(upload_to="uploads/")),
                ("order", models.PositiveIntegerField(default=0)),
                ("original_name", models.CharField(blank=True, max_length=255)),
                ("mime_type", models.CharField(blank=True, max_length=100)),
                ("size_bytes", models.PositiveBigIntegerField(default=0)),
                ("request", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="source_images", to="ai_requests.generationrequest")),
            ],
        ),
        migrations.CreateModel(
            name="UsageLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("provider", models.CharField(max_length=50)),
                ("success", models.BooleanField(default=False)),
                ("credits_used", models.PositiveIntegerField(default=0)),
                ("estimated_cost", models.DecimalField(decimal_places=3, default=0, max_digits=8)),
                ("response_time_ms", models.PositiveIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("request", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="usage_log", to="ai_requests.generationrequest")),
            ],
        ),
    ]
