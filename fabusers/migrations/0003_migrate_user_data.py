from django.db import migrations

def migrate_user_data_forward(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    UserProfile = apps.get_model('fabusers', 'UserProfile')
    
    # Créer un profil pour chaque utilisateur qui n'en a pas encore
    for user in User.objects.all():
        UserProfile.objects.get_or_create(
            user=user,
            defaults={
                'accepts_contact': False,
            }
        )

def migrate_user_data_backward(apps, schema_editor):
    # La migration arrière supprimera automatiquement les profils
    pass

class Migration(migrations.Migration):
    dependencies = [
        ('fabusers', '0002_userprofile'),
    ]

    operations = [
        migrations.RunPython(
            migrate_user_data_forward,
            migrate_user_data_backward
        ),
    ] 