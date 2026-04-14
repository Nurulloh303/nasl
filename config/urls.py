from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

@api_view(["GET"])
@permission_classes([AllowAny])
def healthcheck(request):
    return Response({"status": "ok", "service": "naslai-backend"})

urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", healthcheck),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/v1/auth/", include("apps.accounts.urls")),
    path("api/v1/payment/", include("apps.accounts.payment_urls")),
    path("api/v1/generate/", include("apps.ai_requests.urls")),
    path("api/v1/meta/", include("apps.common.urls")),
    path("api/v1/promo/", include("apps.promo.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
