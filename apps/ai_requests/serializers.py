import json
from rest_framework import serializers

from .models import GenerationAsset, GenerationRequest, UploadedSourceImage
from .prompt_dispatcher import build_prompt

class PromptPreviewSerializer(serializers.Serializer):
    module = serializers.CharField()
    data = serializers.DictField()

    def validate(self, attrs):
        build_prompt(attrs["module"], attrs["data"])
        return attrs

class GenerationSubmitSerializer(serializers.Serializer):
    module = serializers.CharField()
    data = serializers.JSONField(required=False)

    def to_internal_value(self, data):
        mutable = data.copy()
        raw_data = mutable.get("data", {})
        if isinstance(raw_data, str):
            try:
                mutable["data"] = json.loads(raw_data)
            except json.JSONDecodeError:
                raise serializers.ValidationError({"data": "data JSON formatida bo'lishi kerak."})
        elif raw_data in (None, ""):
            mutable["data"] = {}
        return super().to_internal_value(mutable)

    def validate(self, attrs):
        attrs["prompt"] = build_prompt(attrs["module"], attrs["data"])
        return attrs

class UploadedSourceImageSerializer(serializers.ModelSerializer):
    url = serializers.ImageField(source="image", read_only=True)

    class Meta:
        model = UploadedSourceImage
        fields = ("id", "order", "original_name", "mime_type", "size_bytes", "url")

class GenerationAssetSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = GenerationAsset
        fields = ("id", "kind", "order", "mime_type", "text", "url", "metadata")

    def get_url(self, obj):
        return obj.file.url if obj.file else None

class GenerationRequestSerializer(serializers.ModelSerializer):
    assets = GenerationAssetSerializer(many=True, read_only=True)
    source_images = UploadedSourceImageSerializer(many=True, read_only=True)

    class Meta:
        model = GenerationRequest
        fields = (
            "id",
            "module",
            "provider",
            "prompt",
            "payload",
            "status",
            "error_message",
            "input_count",
            "output_count",
            "created_at",
            "started_at",
            "completed_at",
            "source_images",
            "assets",
        )
