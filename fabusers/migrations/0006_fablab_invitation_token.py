# Generated by Django 5.1.4 on 2025-01-24 08:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fabusers', '0005_remove_user_accepts_contact'),
    ]

    operations = [
        migrations.AddField(
            model_name='fablab',
            name='invitation_token',
            field=models.CharField(blank=True, max_length=100, null=True, unique=True, verbose_name="Token d'invitation"),
        ),
    ]
