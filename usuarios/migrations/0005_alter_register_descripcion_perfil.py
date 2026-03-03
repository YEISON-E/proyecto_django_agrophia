from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("usuarios", "0004_remove_shop_state"),
    ]

    operations = [
        migrations.AlterField(
            model_name="register",
            name="descripcion_perfil",
            field=models.CharField(blank=True, max_length=120, null=True),
        ),
    ]
