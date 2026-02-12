import sqlite3
import requests
import time
from datetime import datetime

# --- Configuration ---
DB_NAME = "dmi_weather.db"
API_BASE = "https://opendataapi.dmi.dk/v2/metObs/collections/observation/items"

# We define the data structure here
STATIONS = {
    "06180": "Københavns Lufthavn",
    "06072": "Ødum",
    "06120": "Odense Lufthavn",
    "06190": "Bornholms Lufthavn"
}

PARAMS = {
    "temp_dry": "Temperatur",
    "wind_speed": "Vindhastighed",
    "precip_past10min": "Nedbør 10 min"
}

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # 1. Create Lookup Tables
    c.execute('CREATE TABLE IF NOT EXISTS stations (id INTEGER PRIMARY KEY, dmi_id TEXT UNIQUE, name TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS parameters (id INTEGER PRIMARY KEY, dmi_id TEXT UNIQUE, name TEXT)')
    
    # 2. Create Main Data Table (Note the integer types for IDs)
    c.execute('''
        CREATE TABLE IF NOT EXISTS observations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            station_id INTEGER,
            parameter_id INTEGER,
            observed_at DATETIME,
            value REAL,
            FOREIGN KEY(station_id) REFERENCES stations(id),
            FOREIGN KEY(parameter_id) REFERENCES parameters(id)
        )
    ''')
    
    # 3. Create Indexes (Crucial for performance)
    c.execute('CREATE INDEX IF NOT EXISTS idx_obs_lookup ON observations (station_id, parameter_id, observed_at)')
    c.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_obs ON observations (station_id, parameter_id, observed_at)')
    
    # 4. Populate Lookup Tables (Idempotent: "INSERT OR IGNORE")
    for dmi_id, name in STATIONS.items():
        c.execute('INSERT OR IGNORE INTO stations (dmi_id, name) VALUES (?, ?)', (dmi_id, name))
        
    for dmi_id, name in PARAMS.items():
        c.execute('INSERT OR IGNORE INTO parameters (dmi_id, name) VALUES (?, ?)', (dmi_id, name))
        
    conn.commit()
    conn.close()

def get_lookup_ids():
    """Returns dictionaries to map '06180' -> 1 and 'temp_dry' -> 1"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    station_map = {}
    for row in c.execute('SELECT dmi_id, id FROM stations'):
        station_map[row[0]] = row[1]
        
    param_map = {}
    for row in c.execute('SELECT dmi_id, id FROM parameters'):
        param_map[row[0]] = row[1]
        
    conn.close()
    return station_map, param_map

def fetch_year(station_dmi_id, param_dmi_id, year, s_map, p_map):
    # Convert string IDs to Integer IDs
    s_id_int = s_map[station_dmi_id]
    p_id_int = p_map[param_dmi_id]
    
    # Check if year is already done
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    start_str = f"{year}-01-01"
    end_str = f"{year}-12-31"
    
    c.execute('''
        SELECT COUNT(*) FROM observations 
        WHERE station_id = ? AND parameter_id = ? AND observed_at >= ? AND observed_at <= ?
    ''', (s_id_int, p_id_int, start_str, end_str))
    
    # Threshold: 10-min data = ~52,000 rows/year. 
    # If we have > 50,000, we skip.
    if c.fetchone()[0] > 50000:
        print(f"  [SKIP] {station_dmi_id} {year}: Complete.")
        conn.close()
        return

    conn.close()
    print(f"  [FETCH] {station_dmi_id} {param_dmi_id} {year}...")
    
    # API Request Setup
    start_date = datetime(year, 1, 1)
    end_date = datetime(year, 12, 31, 23, 59, 59)
    if start_date > datetime.now(): return
    if end_date > datetime.now(): end_date = datetime.now()
    
    start_str = start_date.strftime('%Y-%m-%d')
    end_str = end_date.strftime('%Y-%m-%d')
    time_str = f"{start_str}T00:00:00Z/{end_str}T23:59:59Z"
    
    params = {
        'parameterId': param_dmi_id,
        'stationId': station_dmi_id,
        'datetime': time_str,
        'limit': 300000, 
        'api-key': ''
    }
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    offset = 0
    total_inserted = 0

    while True:
        params['offset'] = offset
        try:
            r = requests.get(API_BASE, params=params)
            r.raise_for_status()
            data = r.json()
            features = data.get('features', [])
            
            if not features: break
            
            rows_to_insert = []
            for f in features:
                p = f['properties']
                if p['value'] is not None:
                    # HERE IS THE MAGIC: We insert Integers, not Strings
                    rows_to_insert.append((
                        s_id_int, 
                        p_id_int, 
                        p['observed'], 
                        p['value']
                    ))
            
            if rows_to_insert:
                c.executemany('''
                    INSERT OR IGNORE INTO observations 
                    (station_id, parameter_id, observed_at, value)
                    VALUES (?, ?, ?, ?)
                ''', rows_to_insert)
                conn.commit()
            
            total_inserted += len(rows_to_insert)
            # Minimal logging to keep terminal clean
            if offset % 10000 == 0:
                print(f"    {year}: Inserted {total_inserted} rows...")
            
            if len(features) < 1000: break
            offset += len(features)
            
        except Exception as e:
            print(f"    Error: {e}")
            break
            
    conn.close()

if __name__ == "__main__":
    init_db()
    # Load the maps once to save time
    station_map, param_map = get_lookup_ids()
    
    current_year = datetime.now().year
    
    for station_dmi_id in STATIONS.keys():
        for param_dmi_id in PARAMS.keys():
            for year in range(2011, current_year + 1):
                fetch_year(station_dmi_id, param_dmi_id, year, station_map, param_map)