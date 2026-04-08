from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0007_hash_existing_passwords'),
    ]

    operations = [
        migrations.AddField(
            model_name='register',
            name='failed_login_attempts',
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='register',
            name='blocked_until',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
