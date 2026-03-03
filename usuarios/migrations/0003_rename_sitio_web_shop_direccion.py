from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("usuarios", "0002_register_codigo_reset_and_more"),
    ]

    operations = [
        migrations.RenameField(
            model_name="shop",
            old_name="sitio_web",
            new_name="direccion",
        ),
        migrations.AlterField(
            model_name="shop",
            name="direccion",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
