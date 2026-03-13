from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("blog", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="category",
            name="name_ru",
            field=models.CharField(
                blank=True,
                default="",
                max_length=100,
                verbose_name="Name (Russian)",
            ),
        ),
        migrations.AddField(
            model_name="category",
            name="name_kk",
            field=models.CharField(
                blank=True,
                default="",
                max_length=100,
                verbose_name="Name (Kazakh)",
            ),
        ),
    ]
