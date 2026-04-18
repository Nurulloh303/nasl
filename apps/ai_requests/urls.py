from django.urls import path
from .views import (
    GenerationSubmitView,
    MyGenerationDetailView,
    MyGenerationListView,
    PromptPreviewView,
    generate_image_view,
)

urlpatterns = [
    path("prompt-preview/", PromptPreviewView.as_view(), name="prompt-preview"),
    path("submit/", GenerationSubmitView.as_view(), name="generation-submit"),
    path("requests/", MyGenerationListView.as_view(), name="generation-list"),
    path("requests/<uuid:pk>/", MyGenerationDetailView.as_view(), name="generation-detail"),
    path("generate-image/", generate_image_view, name="generate-image"),
]
