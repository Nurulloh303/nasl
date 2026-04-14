from django.contrib import admin
from .models import GenerationAsset, GenerationRequest, UploadedSourceImage, UsageLog

class GenerationAssetInline(admin.TabularInline):
    model = GenerationAsset
    extra = 0

class UploadedSourceImageInline(admin.TabularInline):
    model = UploadedSourceImage
    extra = 0

@admin.register(GenerationRequest)
class GenerationRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "module", "provider", "status", "created_at")
    list_filter = ("module", "provider", "status")
    search_fields = ("user__username", "prompt", "id")
    inlines = [UploadedSourceImageInline, GenerationAssetInline]

@admin.register(UsageLog)
class UsageLogAdmin(admin.ModelAdmin):
    list_display = ("request", "provider", "success", "credits_used", "estimated_cost", "response_time_ms")
