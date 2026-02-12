import sqlite3
import pandas as pd

DB_FILE = "dmi_stats.db"

def get_station_extremes(station_dmi_id):
    conn = sqlite3.connect(DB_FILE)
    records = {}
    
    def get_stat(param_dmi_id, col_name, order_dir):
        query = f"""
            SELECT s.{col_name}, s.date
            FROM daily_stats s
            JOIN stations st ON s.station_id = st.id
            JOIN parameters p ON s.parameter_id = p.id
            WHERE st.dmi_id = '{station_dmi_id}'
            AND p.dmi_id = '{param_dmi_id}'
            ORDER BY s.{col_name} {order_dir}
            LIMIT 1
        """
        try:
            df = pd.read_sql(query, conn)
            if not df.empty:
                return {'value': df.iloc[0][col_name], 'observed_at': df.iloc[0]['date']}
        except:
            pass
        return None

    records['max_temp'] = get_stat('temp_dry', 'max_val', 'DESC')
    records['min_temp'] = get_stat('temp_dry', 'min_val', 'ASC')
    records['max_wind'] = get_stat('wind_speed', 'max_val', 'DESC')
    
    conn.close()
    return records

def get_monthly_average(station_dmi_id, month_index):
    conn = sqlite3.connect(DB_FILE)
    month_str = f"{month_index:02d}"
    
    query = f"""
        SELECT AVG(s.avg_val) as gennemsnit
        FROM daily_stats s
        JOIN stations st ON s.station_id = st.id
        JOIN parameters p ON s.parameter_id = p.id
        WHERE st.dmi_id = '{station_dmi_id}'
        AND p.dmi_id = 'temp_dry'
        AND strftime('%m', s.date) = '{month_str}'
    """
    
    val = None
    try:
        df = pd.read_sql(query, conn)
        if not df.empty and pd.notna(df['gennemsnit'].iloc[0]):
            val = df['gennemsnit'].iloc[0]
    except:
        pass
        
    conn.close()
    return val