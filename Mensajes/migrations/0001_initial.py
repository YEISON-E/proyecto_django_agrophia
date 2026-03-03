from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("Productos", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="CustomerMessage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("content", models.TextField()),
                ("reply_content", models.TextField(blank=True)),
                ("status", models.CharField(choices=[("pending", "Sin respuesta"), ("replied", "Respondido"), ("rejected", "Rechazado")], default="pending", max_length=12)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("replied_at", models.DateTimeField(blank=True, null=True)),
                ("product", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="messages", to="Productos.product")),
                ("receiver", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="messages_received", to=settings.AUTH_USER_MODEL)),
                ("sender", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="messages_sent", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "db_table": "mensajes_customer_message",
                "ordering": ["-created_at"],
            },
        ),
    ]
