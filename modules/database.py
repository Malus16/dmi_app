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

def get_period_stats_per_year(station_dmi_id, param_dmi_id, start_md, end_md):
    """
    Henter aggregeret statistik (min, max, avg) for en bestemt periode (f.eks. '03-01' til '03-07'),
    grupperet per år historisk for stationen.
    """
    conn = sqlite3.connect(DB_FILE)
    
    # Håndtering af årsskift, f.eks. "12-28" til "01-04"
    if start_md <= end_md:
        date_condition = f"strftime('%m-%d', s.date) >= '{start_md}' AND strftime('%m-%d', s.date) <= '{end_md}'"
        year_grouping = "strftime('%Y', s.date)"
    else:
        # For datoer, der krydser nytår, grupperer vi januar/februar-dagene ind under det foregående års vintersæson.
        date_condition = f"(strftime('%m-%d', s.date) >= '{start_md}' OR strftime('%m-%d', s.date) <= '{end_md}')"
        year_grouping = f"CASE WHEN strftime('%m-%d', s.date) <= '{end_md}' THEN CAST(strftime('%Y', s.date) AS INTEGER) - 1 ELSE CAST(strftime('%Y', s.date) AS INTEGER) END"

    query = f"""
        SELECT 
            {year_grouping} as year,
            MIN(s.min_val) as min_val,
            MAX(s.max_val) as max_val,
            AVG(s.avg_val) as avg_val
        FROM daily_stats s
        JOIN stations st ON s.station_id = st.id
        JOIN parameters p ON s.parameter_id = p.id
        WHERE st.dmi_id = '{station_dmi_id}'
        AND p.dmi_id = '{param_dmi_id}'
        AND {date_condition}
        GROUP BY year
        ORDER BY year ASC
    """
    
    df = pd.DataFrame()
    try:
        df = pd.read_sql(query, conn)
    except Exception as e:
        print(f"Error querying period stats: {e}")
        
    conn.close()
    return df
