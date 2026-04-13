from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("usuarios", "0008_register_failed_login_attempts_and_blocked_until"),
    ]

    operations = [
        migrations.AlterField(
            model_name="register",
            name="descripcion_perfil",
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
