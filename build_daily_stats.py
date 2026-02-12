import sqlite3
import pandas as pd

# Files
SOURCE_DB = "dmi_weather.db"  
TARGET_DB = "dmi_stats.db"    

def create_stats_db():
    conn = sqlite3.connect(TARGET_DB)
    c = conn.cursor()
    
    c.execute('CREATE TABLE IF NOT EXISTS stations (id INTEGER PRIMARY KEY, dmi_id TEXT, name TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS parameters (id INTEGER PRIMARY KEY, dmi_id TEXT, name TEXT)')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS daily_stats (
            station_id INTEGER,
            parameter_id INTEGER,
            date TEXT,          -- "YYYY-MM-DD"
            min_val REAL,
            max_val REAL,
            avg_val REAL,
            count INTEGER,      -- How many readings we based this on (quality check)
            PRIMARY KEY (station_id, parameter_id, date)
        )
    ''')
    conn.commit()
    conn.close()

def aggregate_data():
    source_conn = sqlite3.connect(SOURCE_DB)
    target_conn = sqlite3.connect(TARGET_DB)
    
    print("Reading raw data... (This might take a moment)")
    
    # 1. Copy Lookup Tables first
    print("  Copying lookup tables...")
    df_stations = pd.read_sql("SELECT * FROM stations", source_conn)
    df_stations.to_sql("stations", target_conn, if_exists="replace", index=False)
    
    df_params = pd.read_sql("SELECT * FROM parameters", source_conn)
    df_params.to_sql("parameters", target_conn, if_exists="replace", index=False)
    
    print("  Calculating daily statistics...")
    query = """
        SELECT 
            station_id,
            parameter_id,
            strftime('%Y-%m-%d', observed_at) as date,
            MIN(value) as min_val,
            MAX(value) as max_val,
            AVG(value) as avg_val,
            COUNT(value) as count
        FROM observations
        GROUP BY station_id, parameter_id, date
    """
    
    df_daily = pd.read_sql(query, source_conn)
    
    print(f"  Writing {len(df_daily)} aggregated rows to {TARGET_DB}...")
    
    df_daily.to_sql("daily_stats", target_conn, if_exists="replace", index=False)
    
    # Create an index for speed
    target_conn.execute("CREATE INDEX IF NOT EXISTS idx_date ON daily_stats (date)")
    
    source_conn.close()
    target_conn.close()
    print("Done! 'dmi_stats.db' is ready for deployment.")

if __name__ == "__main__":
    create_stats_db()
    aggregate_data()