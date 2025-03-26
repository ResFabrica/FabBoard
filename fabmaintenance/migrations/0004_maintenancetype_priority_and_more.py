# Generated by Django 5.1.4 on 2025-03-25 21:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fabmaintenance', '0003_alter_machine_options_alter_machinetype_options_and_more'),
        ('fabusers', '0006_fablab_invitation_token'),
    ]

    operations = [
        migrations.AddField(
            model_name='maintenancetype',
            name='priority',
            field=models.IntegerField(choices=[(1, 'Basse'), (2, 'Moyenne'), (3, 'Haute'), (4, 'Critique')], default=2, verbose_name='Priorité'),
        ),
        migrations.AlterField(
            model_name='maintenance',
            name='scheduled_date',
            field=models.DateField(verbose_name='Date prévue'),
        ),
        migrations.AlterUniqueTogether(
            name='machine',
            unique_together={('name', 'fablab')},
        ),
    ]
