from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('fabmaintenance', '0003_alter_machine_options_alter_machinetype_options_and_more'),
    ]

    operations = [
        # Ajouter les champs instructions et required_tools à la table Maintenance
        migrations.AddField(
            model_name='maintenance',
            name='instructions',
            field=models.TextField(blank=True, null=True, verbose_name='Instructions'),
        ),
        migrations.AddField(
            model_name='maintenance',
            name='required_tools',
            field=models.TextField(blank=True, null=True, verbose_name='Outils nécessaires'),
        ),
        
        # Supprimer le champ machine_type_id de la table MaintenanceType
        migrations.RemoveField(
            model_name='maintenancetype',
            name='machine_type',
        ),
    ] 