from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="profile",
            name="telegram_id",
            field=models.CharField(
                max_length=100,
                unique=True,
                null=True,
                blank=True,
                db_index=True,
            ),
        ),
    ]
