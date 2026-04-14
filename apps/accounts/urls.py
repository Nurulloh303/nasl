from django.urls import path
from .views import LoginView, MeView, RegisterView, TelegramAuthView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("telegram-auth/", TelegramAuthView.as_view(), name="telegram-auth"),
    path("me/", MeView.as_view(), name="me"),
]
