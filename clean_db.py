import sqlite3

DB_NAME = "dmi_weather.db"
STATION_DMI_ID = "06071"  # The one to remove

conn = sqlite3.connect(DB_NAME)
c = conn.cursor()

try:
    # 1. Find the internal Integer ID
    c.execute("SELECT id, name FROM stations WHERE dmi_id = ?", (STATION_DMI_ID,))
    result = c.fetchone()
    
    if result:
        internal_id, name = result
        print(f"Found '{name}' (ID: {internal_id}). Preparing to delete...")
        
        # 2. Delete all observations first
        c.execute("DELETE FROM observations WHERE station_id = ?", (internal_id,))
        rows_deleted = c.rowcount
        print(f"  - Deleted {rows_deleted} rows of bad data.")
        
        # 3. Delete the station from the lookup table
        c.execute("DELETE FROM stations WHERE id = ?", (internal_id,))
        print("  - Deleted station from lookup table.")
        
        conn.commit()
        print("Success.")
        
    else:
        print(f"Station {STATION_DMI_ID} not found in database.")

except Exception as e:
    print(f"Error: {e}")
    conn.rollback()

finally:
    conn.close()