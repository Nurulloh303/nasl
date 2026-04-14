from django.urls import path
from .views import ModuleMetaView

urlpatterns = [
    path("modules/", ModuleMetaView.as_view(), name="module-meta"),
]
