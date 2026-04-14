from django.apps import AppConfig

class AiRequestsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.ai_requests"

    def ready(self):
        import apps.accounts.signals  # noqa
