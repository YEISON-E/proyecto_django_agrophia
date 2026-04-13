from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('Productos', '0007_alter_product_unidad'),
    ]

    operations = [
        migrations.RenameField(
            model_name='product',
            old_name='garantia',
            new_name='tiempo_durabilidad',
        ),
    ]
