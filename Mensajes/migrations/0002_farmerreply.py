from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("Mensajes", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="FarmerReply",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("content", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "message",
                    models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="farmer_replies", to="Mensajes.customermessage"),
                ),
            ],
            options={
                "db_table": "mensajes_farmer_reply",
                "ordering": ["created_at"],
            },
        ),
    ]
