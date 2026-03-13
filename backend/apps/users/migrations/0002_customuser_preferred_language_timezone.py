# Generated migration for preferred_language and timezone fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="customuser",
            name="preferred_language",
            field=models.CharField(
                choices=[
                    ("en", "English"),
                    ("ru", "Russian"),
                    ("kk", "Kazakh"),
                ],
                default="en",
                max_length=10,
            ),
        ),
        migrations.AddField(
            model_name="customuser",
            name="timezone",
            field=models.CharField(default="UTC", max_length=50),
        ),
    ]
