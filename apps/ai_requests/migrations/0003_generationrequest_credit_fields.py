from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ai_requests", "0002_generationrequest_ai_requests_user_id_988af1_idx_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="generationrequest",
            name="credits_charged",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="generationrequest",
            name="credits_refunded",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="generationrequest",
            name="used_free_generation",
            field=models.BooleanField(default=False),
        ),
    ]
