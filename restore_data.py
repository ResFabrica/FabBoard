import sqlite3
import sys

def restore_data():
    # Connect to both databases
    backup_conn = sqlite3.connect('db.sqlite3.backup_migration')
    current_conn = sqlite3.connect('db.sqlite3')
    
    try:
        backup_cursor = backup_conn.cursor()
        current_cursor = current_conn.cursor()
        
        # Supprimer toutes les données existantes dans l'ordre inverse des dépendances
        print("Nettoyage des données existantes...")
        tables = [
            "fabprojects_customfieldvalue",
            "fabprojects_subtask",
            "fabprojects_task_tags",
            "fabprojects_task_assigned_users",
            "fabprojects_task",
            "fabprojects_customfield",
            "fabprojects_tag",
            "fabprojects_section",
            "fabprojects_view",
            "fabmaintenance_maintenance",
            "fabmaintenance_maintenancetype",
            "fabmaintenance_machine",
            "fabmaintenance_machinetype",
            "fabusers_fablab_users",
            "fabusers_fablab",
            "auth_user"
        ]
        
        for table in tables:
            current_cursor.execute(f"DELETE FROM {table}")
        
        # Restaurer les utilisateurs
        print("Restauration des utilisateurs...")
        backup_cursor.execute("SELECT * FROM auth_user")
        users = backup_cursor.fetchall()
        
        for user in users:
            current_cursor.execute(
                """INSERT INTO auth_user 
                   (id, password, last_login, is_superuser, username, first_name,
                    last_name, email, is_staff, is_active, date_joined,
                    accepts_contact, fablab_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                user
            )
        
        # Restaurer les FabLabs
        print("Restauration des FabLabs...")
        backup_cursor.execute("SELECT * FROM fabusers_fablab")
        fablabs = backup_cursor.fetchall()
        
        for fablab in fablabs:
            current_cursor.execute(
                "INSERT INTO fabusers_fablab (id, name, address) VALUES (?, ?, ?)",
                (fablab[0], fablab[1], fablab[2])
            )
        
        # Restaurer les relations utilisateurs-fablabs
        print("Restauration des relations utilisateurs-fablabs...")
        backup_cursor.execute("SELECT * FROM fabusers_fablab_users")
        fablab_users = backup_cursor.fetchall()
        
        for relation in fablab_users:
            # Mettre à jour le fablab_id dans auth_user
            current_cursor.execute(
                "UPDATE auth_user SET fablab_id = ? WHERE id = ?",
                (relation[1], relation[2])
            )
            # Insérer aussi dans la table de relation many-to-many
            current_cursor.execute(
                """INSERT OR IGNORE INTO fabusers_fablab_users 
                   (fablab_id, user_id) VALUES (?, ?)""",
                (relation[1], relation[2])
            )
        
        # Restaurer les types de machines
        print("Restauration des types de machines...")
        backup_cursor.execute("SELECT * FROM fabmaintenance_machinetype")
        machine_types = backup_cursor.fetchall()
        
        for machine_type in machine_types:
            current_cursor.execute(
                "INSERT INTO fabmaintenance_machinetype (id, name) VALUES (?, ?)",
                (machine_type[0], machine_type[1])
            )
        
        # Restaurer les machines
        print("Restauration des machines...")
        backup_cursor.execute("""
            SELECT m.id, m.name, m.serial_number, m.image, m.machine_type_id, f.id
            FROM fabmaintenance_machine m
            JOIN fabusers_fablab f ON f.id = m.fablab_id
        """)
        machines = backup_cursor.fetchall()
        
        for machine in machines:
            current_cursor.execute(
                "INSERT INTO fabmaintenance_machine (id, name, serial_number, image, machine_type_id, fablab_id) VALUES (?, ?, ?, ?, ?, ?)",
                machine
            )
        
        # Restaurer les types de maintenance
        print("Restauration des types de maintenance...")
        backup_cursor.execute("SELECT * FROM fabmaintenance_maintenancetype")
        maintenance_types = backup_cursor.fetchall()
        
        for maintenance_type in maintenance_types:
            current_cursor.execute(
                """INSERT INTO fabmaintenance_maintenancetype 
                   (id, name, machine_type_id, is_custom, period_days, description)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                maintenance_type
            )
        
        # Restaurer les maintenances
        print("Restauration des maintenances...")
        backup_cursor.execute("SELECT * FROM fabmaintenance_maintenance")
        maintenances = backup_cursor.fetchall()
        
        for maintenance in maintenances:
            # Réorganiser les données dans le bon ordre
            # [id, scheduled_date, completed_date, notes, machine_id, maintenance_type_id, period_days, scheduling_type, custom_type_name, significant]
            current_cursor.execute(
                """INSERT INTO fabmaintenance_maintenance 
                   (id, scheduled_date, completed_date, notes, scheduling_type, 
                    period_days, custom_type_name, significant, completed_by_id,
                    machine_id, maintenance_type_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (maintenance[0],  # id
                 maintenance[1],  # scheduled_date
                 maintenance[2],  # completed_date
                 maintenance[3] or '',  # notes (default empty string if NULL)
                 maintenance[7] or 'periodic',  # scheduling_type (default 'periodic' if NULL)
                 maintenance[6],  # period_days
                 maintenance[8],  # custom_type_name
                 maintenance[9] if maintenance[9] is not None else False,  # significant (default False if NULL)
                 maintenance[4],  # completed_by_id
                 maintenance[5],  # machine_id
                 maintenance[6])  # maintenance_type_id
            )
        
        # Restaurer les vues
        print("Restauration des vues...")
        backup_cursor.execute("SELECT * FROM fabprojects_view")
        views = backup_cursor.fetchall()
        
        for view in views:
            current_cursor.execute(
                """INSERT INTO fabprojects_view 
                   (id, name, created_at, updated_at, fablab_id)
                   VALUES (?, ?, ?, ?, ?)""",
                view
            )
        
        # Restaurer les sections
        print("Restauration des sections...")
        backup_cursor.execute("SELECT * FROM fabprojects_section")
        sections = backup_cursor.fetchall()
        
        for section in sections:
            current_cursor.execute(
                """INSERT INTO fabprojects_section 
                   (id, name, "order", created_at, updated_at, view_id)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                section
            )
        
        # Restaurer les tags
        print("Restauration des tags...")
        backup_cursor.execute("SELECT * FROM fabprojects_tag")
        tags = backup_cursor.fetchall()
        
        for tag in tags:
            current_cursor.execute(
                "INSERT INTO fabprojects_tag (id, name, color, fablab_id) VALUES (?, ?, ?, ?)",
                tag
            )
        
        # Restaurer les champs personnalisés
        print("Restauration des champs personnalisés...")
        backup_cursor.execute("SELECT * FROM fabprojects_customfield")
        custom_fields = backup_cursor.fetchall()
        
        for field in custom_fields:
            current_cursor.execute(
                """INSERT INTO fabprojects_customfield 
                   (id, name, field_type, choices, fablab_id)
                   VALUES (?, ?, ?, ?, ?)""",
                field
            )
        
        # Restaurer les tâches
        print("Restauration des tâches...")
        backup_cursor.execute("SELECT * FROM fabprojects_task")
        tasks = backup_cursor.fetchall()
        
        for task in tasks:
            current_cursor.execute(
                """INSERT INTO fabprojects_task 
                   (id, title, description, deadline, is_completed, "order",
                    created_at, updated_at, section_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                task
            )
        
        # Restaurer les relations tâches-utilisateurs
        print("Restauration des assignations de tâches...")
        backup_cursor.execute("SELECT * FROM fabprojects_task_assigned_users")
        task_users = backup_cursor.fetchall()
        
        for relation in task_users:
            current_cursor.execute(
                "INSERT INTO fabprojects_task_assigned_users (task_id, user_id) VALUES (?, ?)",
                (relation[1], relation[2])
            )
        
        # Restaurer les relations tâches-tags
        print("Restauration des tags de tâches...")
        backup_cursor.execute("SELECT * FROM fabprojects_task_tags")
        task_tags = backup_cursor.fetchall()
        
        for relation in task_tags:
            current_cursor.execute(
                "INSERT INTO fabprojects_task_tags (task_id, tag_id) VALUES (?, ?)",
                (relation[1], relation[2])
            )
        
        # Restaurer les sous-tâches
        print("Restauration des sous-tâches...")
        backup_cursor.execute("SELECT * FROM fabprojects_subtask")
        subtasks = backup_cursor.fetchall()
        
        for subtask in subtasks:
            current_cursor.execute(
                """INSERT INTO fabprojects_subtask 
                   (id, title, is_completed, order, created_at, updated_at, task_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                subtask
            )
        
        # Restaurer les valeurs des champs personnalisés
        print("Restauration des valeurs des champs personnalisés...")
        backup_cursor.execute("SELECT * FROM fabprojects_customfieldvalue")
        field_values = backup_cursor.fetchall()
        
        for value in field_values:
            current_cursor.execute(
                """INSERT INTO fabprojects_customfieldvalue 
                   (id, value, field_id, task_id)
                   VALUES (?, ?, ?, ?)""",
                value
            )
        
        current_conn.commit()
        print("Restauration terminée avec succès!")
        
    except Exception as e:
        print(f"Erreur lors de la restauration : {e}")
        current_conn.rollback()
    finally:
        backup_conn.close()
        current_conn.close()

if __name__ == '__main__':
    restore_data() 