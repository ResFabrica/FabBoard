import sqlite3
import os
import json
from datetime import datetime

def connect_db(db_path):
    return sqlite3.connect(db_path)

def table_exists(cursor, table_name):
    cursor.execute(f"""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='{table_name}'
    """)
    return cursor.fetchone() is not None

def clear_table(cursor, table_name):
    cursor.execute(f"DELETE FROM {table_name}")

def migrate_data():
    old_db = connect_db('db.sqlite3.bak')
    new_db = connect_db('db.sqlite3')
    
    try:
        old_cursor = old_db.cursor()
        new_cursor = new_db.cursor()

        # Migrer les utilisateurs d'abord
        print("Migrating Users...")
        clear_table(new_cursor, "auth_user")
        
        # Ajouter les colonnes accepts_contact et fablab_id si elles n'existent pas
        new_cursor.execute("""
            CREATE TABLE IF NOT EXISTS temp_auth_user (
                id INTEGER PRIMARY KEY,
                password VARCHAR(128) NOT NULL,
                last_login DATETIME NULL,
                is_superuser BOOL NOT NULL,
                username VARCHAR(150) NOT NULL UNIQUE,
                first_name VARCHAR(150) NOT NULL,
                last_name VARCHAR(150) NOT NULL,
                email VARCHAR(254) NOT NULL,
                is_staff BOOL NOT NULL,
                is_active BOOL NOT NULL,
                date_joined DATETIME NOT NULL,
                accepts_contact BOOL NOT NULL DEFAULT 0,
                fablab_id INTEGER NULL REFERENCES fabmaintenance_fablab(id)
            )
        """)
        
        old_cursor.execute("""
            SELECT id, password, last_login, is_superuser, username, first_name, 
                   last_name, email, is_staff, is_active, date_joined
            FROM auth_user
        """)
        users = old_cursor.fetchall()
        
        for user in users:
            try:
                new_cursor.execute("""
                    INSERT INTO temp_auth_user 
                    (id, password, last_login, is_superuser, username, first_name, 
                     last_name, email, is_staff, is_active, date_joined, accepts_contact)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
                """, user)
            except sqlite3.IntegrityError as e:
                print(f"Error inserting User {user[4]}: {e}")
        
        # Migrer les FabLabs
        print("Migrating FabLabs...")
        clear_table(new_cursor, "fabmaintenance_fablab")
        old_cursor.execute("SELECT id, name, address FROM fabmaintenance_fablab")
        fablabs = old_cursor.fetchall()
        
        for fablab in fablabs:
            try:
                new_cursor.execute(
                    "INSERT INTO fabmaintenance_fablab (id, name, address) VALUES (?, ?, ?)",
                    fablab
                )
            except sqlite3.IntegrityError as e:
                print(f"Error inserting FabLab {fablab[1]}: {e}")

        # Migrer les relations User-FabLab
        print("Migrating User-FabLab relationships...")
        clear_table(new_cursor, "fabmaintenance_fablab_users")
        old_cursor.execute("SELECT fablab_id, user_id FROM fabmaintenance_fablab_users")
        fablab_users = old_cursor.fetchall()
        
        for relation in fablab_users:
            try:
                new_cursor.execute(
                    "INSERT INTO fabmaintenance_fablab_users (fablab_id, user_id) VALUES (?, ?)",
                    relation
                )
            except sqlite3.IntegrityError as e:
                print(f"Error inserting FabLab-User relation {relation}: {e}")

        # Migrer les attributs supplémentaires des utilisateurs
        print("Migrating User additional attributes...")
        old_cursor.execute("SELECT id, fablab_id FROM auth_user")
        user_attrs = old_cursor.fetchall()
        
        for user_attr in user_attrs:
            if user_attr[1] is not None:  # Si l'utilisateur a un fablab par défaut
                try:
                    new_cursor.execute(
                        "UPDATE temp_auth_user SET fablab_id = ? WHERE id = ?",
                        (user_attr[1], user_attr[0])
                    )
                except sqlite3.IntegrityError as e:
                    print(f"Error updating User {user_attr[0]} attributes: {e}")
        
        # Remplacer la table auth_user par temp_auth_user
        new_cursor.execute("DROP TABLE auth_user")
        new_cursor.execute("ALTER TABLE temp_auth_user RENAME TO auth_user")
        
        # Migrer les MachineTypes
        print("Migrating MachineTypes...")
        clear_table(new_cursor, "fabmaintenance_machinetype")
        old_cursor.execute("SELECT id, name, description FROM fabmaintenance_machinetype")
        machine_types = old_cursor.fetchall()
        
        for machine_type in machine_types:
            try:
                new_cursor.execute(
                    "INSERT INTO fabmaintenance_machinetype (id, name, description) VALUES (?, ?, ?)",
                    machine_type
                )
            except sqlite3.IntegrityError as e:
                print(f"Error inserting MachineType {machine_type[1]}: {e}")
        
        # Migrer les Machines
        print("Migrating Machines...")
        clear_table(new_cursor, "fabmaintenance_machine")
        old_cursor.execute("SELECT id, name, machine_type_id, fablab_id, serial_number, image FROM fabmaintenance_machine")
        machines = old_cursor.fetchall()
        
        for machine in machines:
            try:
                new_cursor.execute(
                    "INSERT INTO fabmaintenance_machine (id, name, machine_type_id, fablab_id, serial_number, image) VALUES (?, ?, ?, ?, ?, ?)",
                    machine
                )
            except sqlite3.IntegrityError as e:
                print(f"Error inserting Machine {machine[1]}: {e}")
        
        # Migrer les MaintenanceTypes
        print("Migrating MaintenanceTypes...")
        clear_table(new_cursor, "fabmaintenance_maintenancetype")
        old_cursor.execute("SELECT id, name, machine_type_id, period_days, description, is_custom FROM fabmaintenance_maintenancetype")
        maintenance_types = old_cursor.fetchall()
        
        for maintenance_type in maintenance_types:
            try:
                new_cursor.execute(
                    "INSERT INTO fabmaintenance_maintenancetype (id, name, machine_type_id, period_days, description, is_custom) VALUES (?, ?, ?, ?, ?, ?)",
                    maintenance_type
                )
            except sqlite3.IntegrityError as e:
                print(f"Error inserting MaintenanceType {maintenance_type[1]}: {e}")
        
        # Migrer les Maintenances
        print("Migrating Maintenances...")
        clear_table(new_cursor, "fabmaintenance_maintenance")
        old_cursor.execute("""
            SELECT id, machine_id, maintenance_type_id, scheduled_date, completed_date, 
                   completed_by_id, notes, scheduling_type, period_days, custom_type_name, significant 
            FROM fabmaintenance_maintenance
        """)
        maintenances = old_cursor.fetchall()
        
        for maintenance in maintenances:
            try:
                new_cursor.execute("""
                    INSERT INTO fabmaintenance_maintenance 
                    (id, machine_id, maintenance_type_id, scheduled_date, completed_date, 
                     completed_by_id, notes, scheduling_type, period_days, custom_type_name, significant)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, maintenance)
            except sqlite3.IntegrityError as e:
                print(f"Error inserting Maintenance {maintenance[0]}: {e}")
        
        # Vérifier si les tables de fabprojects existent
        if table_exists(old_cursor, "fabprojects_view"):
            # Migrer les Views
            print("Migrating Views...")
            clear_table(new_cursor, "fabprojects_view")
            old_cursor.execute("SELECT id, name, fablab_id, created_at, updated_at FROM fabprojects_view")
            views = old_cursor.fetchall()
            
            for view in views:
                try:
                    new_cursor.execute(
                        "INSERT INTO fabprojects_view (id, name, fablab_id, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                        view
                    )
                except sqlite3.IntegrityError as e:
                    print(f"Error inserting View {view[1]}: {e}")
            
            # Migrer les Sections
            print("Migrating Sections...")
            clear_table(new_cursor, "fabprojects_section")
            old_cursor.execute("SELECT id, name, view_id, order, created_at, updated_at FROM fabprojects_section")
            sections = old_cursor.fetchall()
            
            for section in sections:
                try:
                    new_cursor.execute(
                        "INSERT INTO fabprojects_section (id, name, view_id, order, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                        section
                    )
                except sqlite3.IntegrityError as e:
                    print(f"Error inserting Section {section[1]}: {e}")
            
            # Migrer les Tags
            print("Migrating Tags...")
            clear_table(new_cursor, "fabprojects_tag")
            old_cursor.execute("SELECT id, name, color, fablab_id FROM fabprojects_tag")
            tags = old_cursor.fetchall()
            
            for tag in tags:
                try:
                    new_cursor.execute(
                        "INSERT INTO fabprojects_tag (id, name, color, fablab_id) VALUES (?, ?, ?, ?)",
                        tag
                    )
                except sqlite3.IntegrityError as e:
                    print(f"Error inserting Tag {tag[1]}: {e}")
            
            # Migrer les CustomFields
            print("Migrating CustomFields...")
            clear_table(new_cursor, "fabprojects_customfield")
            old_cursor.execute("SELECT id, name, field_type, choices, fablab_id FROM fabprojects_customfield")
            custom_fields = old_cursor.fetchall()
            
            for custom_field in custom_fields:
                try:
                    new_cursor.execute(
                        "INSERT INTO fabprojects_customfield (id, name, field_type, choices, fablab_id) VALUES (?, ?, ?, ?, ?)",
                        custom_field
                    )
                except sqlite3.IntegrityError as e:
                    print(f"Error inserting CustomField {custom_field[1]}: {e}")
            
            # Migrer les Tasks
            print("Migrating Tasks...")
            clear_table(new_cursor, "fabprojects_task")
            old_cursor.execute("""
                SELECT id, title, description, section_id, deadline, is_completed, order,
                       created_at, updated_at
                FROM fabprojects_task
            """)
            tasks = old_cursor.fetchall()
            
            for task in tasks:
                try:
                    new_cursor.execute("""
                        INSERT INTO fabprojects_task 
                        (id, title, description, section_id, deadline, is_completed, order,
                         created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, task)
                except sqlite3.IntegrityError as e:
                    print(f"Error inserting Task {task[1]}: {e}")
            
            # Migrer les relations many-to-many
            print("Migrating many-to-many relationships...")
            
            # Tasks - Tags
            clear_table(new_cursor, "fabprojects_task_tags")
            old_cursor.execute("SELECT task_id, tag_id FROM fabprojects_task_tags")
            task_tags = old_cursor.fetchall()
            for relation in task_tags:
                try:
                    new_cursor.execute(
                        "INSERT INTO fabprojects_task_tags (task_id, tag_id) VALUES (?, ?)",
                        relation
                    )
                except sqlite3.IntegrityError as e:
                    print(f"Error inserting Task-Tag relation {relation}: {e}")
            
            # Tasks - Users
            clear_table(new_cursor, "fabprojects_task_assigned_users")
            old_cursor.execute("SELECT task_id, user_id FROM fabprojects_task_assigned_users")
            task_users = old_cursor.fetchall()
            for relation in task_users:
                try:
                    new_cursor.execute(
                        "INSERT INTO fabprojects_task_assigned_users (task_id, user_id) VALUES (?, ?)",
                        relation
                    )
                except sqlite3.IntegrityError as e:
                    print(f"Error inserting Task-User relation {relation}: {e}")
            
            # Views - CustomFields
            clear_table(new_cursor, "fabprojects_view_custom_fields")
            old_cursor.execute("SELECT view_id, customfield_id FROM fabprojects_view_custom_fields")
            view_fields = old_cursor.fetchall()
            for relation in view_fields:
                try:
                    new_cursor.execute(
                        "INSERT INTO fabprojects_view_custom_fields (view_id, customfield_id) VALUES (?, ?)",
                        relation
                    )
                except sqlite3.IntegrityError as e:
                    print(f"Error inserting View-CustomField relation {relation}: {e}")
            
            # Migrer les CustomFieldValues
            print("Migrating CustomFieldValues...")
            clear_table(new_cursor, "fabprojects_customfieldvalue")
            old_cursor.execute("SELECT id, task_id, field_id, value FROM fabprojects_customfieldvalue")
            field_values = old_cursor.fetchall()
            
            for field_value in field_values:
                try:
                    new_cursor.execute(
                        "INSERT INTO fabprojects_customfieldvalue (id, task_id, field_id, value) VALUES (?, ?, ?, ?)",
                        field_value
                    )
                except sqlite3.IntegrityError as e:
                    print(f"Error inserting CustomFieldValue {field_value[0]}: {e}")
            
            # Migrer les SubTasks
            print("Migrating SubTasks...")
            clear_table(new_cursor, "fabprojects_subtask")
            old_cursor.execute("""
                SELECT id, title, task_id, is_completed, order, created_at, updated_at 
                FROM fabprojects_subtask
            """)
            subtasks = old_cursor.fetchall()
            
            for subtask in subtasks:
                try:
                    new_cursor.execute("""
                        INSERT INTO fabprojects_subtask 
                        (id, title, task_id, is_completed, order, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, subtask)
                except sqlite3.IntegrityError as e:
                    print(f"Error inserting SubTask {subtask[1]}: {e}")
        else:
            print("fabprojects tables not found in old database, skipping...")
        
        # Commit les changements
        new_db.commit()
        print("Migration completed successfully!")
        
    except Exception as e:
        print(f"An error occurred during migration: {e}")
        new_db.rollback()
        raise
    finally:
        old_db.close()
        new_db.close()

if __name__ == "__main__":
    if not os.path.exists('db.sqlite3.bak'):
        print("Error: db.sqlite3.bak not found!")
        exit(1)
    
    if not os.path.exists('db.sqlite3'):
        print("Error: db.sqlite3 not found!")
        exit(1)
    
    migrate_data() 