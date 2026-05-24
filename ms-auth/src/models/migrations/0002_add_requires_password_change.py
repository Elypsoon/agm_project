# Migration: adds requires_password_change field to the User model.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('models', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='requires_password_change',
            field=models.BooleanField(default=True),
        ),
    ]
