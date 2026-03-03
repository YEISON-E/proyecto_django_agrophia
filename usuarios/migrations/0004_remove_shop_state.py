from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("usuarios", "0003_rename_sitio_web_shop_direccion"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.DeleteModel(name="Shop"),
            ],
        ),
    ]
