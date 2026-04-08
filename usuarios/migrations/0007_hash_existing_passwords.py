from django.db import migrations
from django.contrib.auth.hashers import identify_hasher, make_password


def hash_register_passwords(apps, schema_editor):
    Register = apps.get_model('usuarios', 'Register')

    for register in Register.objects.all().only('id', 'contrasena'):
        raw_or_hashed = (register.contrasena or '').strip()
        if not raw_or_hashed:
            continue

        try:
            identify_hasher(raw_or_hashed)
            # Already hashed in Django format.
            continue
        except Exception:
            register.contrasena = make_password(raw_or_hashed)
            register.save(update_fields=['contrasena'])


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0006_register_admin_code_validated'),
    ]

    operations = [
        migrations.RunPython(hash_register_passwords, migrations.RunPython.noop),
    ]
