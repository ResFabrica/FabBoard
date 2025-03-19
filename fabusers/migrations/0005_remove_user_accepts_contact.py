from django.db import migrations

def remove_accepts_contact(apps, schema_editor):
    # Utiliser le schéma SQLite pour supprimer la colonne
    schema_editor.execute(
        "CREATE TABLE auth_user_new ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "password VARCHAR(128) NOT NULL, "
        "last_login DATETIME NULL, "
        "is_superuser BOOL NOT NULL, "
        "username VARCHAR(150) NOT NULL UNIQUE, "
        "first_name VARCHAR(150) NOT NULL, "
        "last_name VARCHAR(150) NOT NULL, "
        "email VARCHAR(254) NOT NULL, "
        "is_staff BOOL NOT NULL, "
        "is_active BOOL NOT NULL, "
        "date_joined DATETIME NOT NULL)"
    )
    
    schema_editor.execute(
        "INSERT INTO auth_user_new "
        "SELECT id, password, last_login, is_superuser, username, first_name, "
        "last_name, email, is_staff, is_active, date_joined FROM auth_user"
    )
    
    schema_editor.execute("DROP TABLE auth_user")
    schema_editor.execute("ALTER TABLE auth_user_new RENAME TO auth_user")

class Migration(migrations.Migration):
    dependencies = [
        ('fabusers', '0004_userprofile_avatar_color'),
    ]

    operations = [
        migrations.RunPython(remove_accepts_contact),
    ] 