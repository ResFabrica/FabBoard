import sqlite3
import sys

def restore_fablabs():
    # Connect to both databases
    backup_conn = sqlite3.connect('db.sqlite3.bak')
    current_conn = sqlite3.connect('db.sqlite3')
    
    try:
        # Get FabLabs from backup
        backup_cursor = backup_conn.cursor()
        backup_cursor.execute("SELECT * FROM fabmaintenance_fablab")
        fablabs = backup_cursor.fetchall()
        
        if not fablabs:
            print("No FabLabs found in backup database!")
            return
        
        # Get column names from source table
        backup_cursor.execute("PRAGMA table_info(fabmaintenance_fablab)")
        source_columns = [col[1] for col in backup_cursor.fetchall()]
        
        # Get column names from destination table
        current_cursor = current_conn.cursor()
        current_cursor.execute("PRAGMA table_info(fabusers_fablab)")
        dest_columns = [col[1] for col in current_cursor.fetchall()]
        
        # Find common columns between source and destination
        common_columns = [col for col in source_columns if col in dest_columns]
        
        # Delete existing FabLabs in current database (both tables)
        current_cursor.execute("DELETE FROM fabusers_fablab")
        current_cursor.execute("DELETE FROM fabmaintenance_fablab")
        
        # Prepare data for insertion (only common columns)
        column_indices = [source_columns.index(col) for col in common_columns]
        fablabs_filtered = [[row[i] for i in column_indices] for row in fablabs]
        
        # Insert FabLabs into new table
        placeholders = ','.join(['?' for _ in common_columns])
        insert_query = f"INSERT INTO fabusers_fablab ({','.join(common_columns)}) VALUES ({placeholders})"
        
        current_cursor.executemany(insert_query, fablabs_filtered)
        current_conn.commit()
        
        print(f"Successfully restored {len(fablabs)} FabLabs to fabusers_fablab!")
        print("Cleaned up fabmaintenance_fablab table.")
        
    finally:
        backup_conn.close()
        current_conn.close()

if __name__ == '__main__':
    restore_fablabs() 