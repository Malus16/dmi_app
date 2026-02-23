import requests
import pandas as pd
import streamlit as st 

API_BASE = "https://opendataapi.dmi.dk/v2/metObs/collections/observation/items"

KNOWN_PARAMS_DK = {
    "temp_dry": "Temperatur",
    "precip_past1h": "Nedbør (sidste time)",
    "precip_past24h": "Nedbør (seneste 24 timer)",
    "wind_speed": "Vindhastighed",  
    "humidity": "Luftfugtighed",
    "pressure": "Lufttryk",
    "sun_last1h_glob": "Solskinstimer",
    "visibility": "Sigtbarhed",
    "cloud_cover": "Skydække",
    "cloud_height": "Skyhøjde",
    "wind_dir": "Vindretning",
    "temp_soil": "Jordtemperatur",
    "temp_dew": "Dugpunkt",
    "temp_grass": "Græstemperatur"
}

def get_param_name(param_id):
    if param_id in KNOWN_PARAMS_DK:
        return KNOWN_PARAMS_DK[param_id]
    return param_id.replace('_', ' ').capitalize()

# Stationer (Navn -> ID) og parameter data
_station_data = pd.read_csv("DMI stations.csv", dtype=str)
STATIONS = dict(zip(_station_data['StationName'], _station_data['StationId']))

# Alle parameter_kolonner fra CSV filen (de starter efter StationId og StationName)
ALL_PARAM_COLUMNS = list(_station_data.columns)[2:]

# Byg PARAMS mapping (Display Navn -> DMI ID) for alle mulige parametre
PARAMS = {}
for p in ALL_PARAM_COLUMNS:
    PARAMS[get_param_name(p)] = p

# Station -> { param_id : start_year } mapping
STATION_AVAILABLE_PARAMS = {}
for _, row in _station_data.iterrows():
    stat_id = row['StationId']
    p_dict = {}
    for col in ALL_PARAM_COLUMNS:
        val = row[col]
        if pd.notna(val) and val != '-':
            p_dict[col] = int(val)
    STATION_AVAILABLE_PARAMS[stat_id] = p_dict

def fetch_dmi_data(station_id, param_id, start_date, end_date):
    # Formater datoer til RFC3339
    time_str = f"{start_date.isoformat()}T00:00:00Z/{end_date.isoformat()}T23:59:59Z"
    
    # Base parametre
    params = {
        'parameterId': param_id,
        'stationId': station_id,
        'datetime': time_str,
        'limit': 1000, 
        'api-key': ''   
    }
    
    all_features = []
    offset = 0
    
    # Statusbesked
    status_text = st.empty()
    
    try:
        while True:
            # Opdater offset for at hente næste side
            params['offset'] = offset
            
            status_text.text(f"Henter data... (Række {offset} fundet indtil videre)")
            
            response = requests.get(API_BASE, params=params)
            response.raise_for_status()
            data = response.json()
            
            features = data.get('features', [])
            all_features.extend(features)
            
            # Hvis vi fik færre end 1000 rækker, er vi færdige
            if len(features) < 1000:
                break
            
            # Ellers gør klar til næste side
            offset += 1000
            
        # Ryd statusbesked når færdig
        status_text.empty()
        
        if not all_features:
            return pd.DataFrame()
            
        # Behandl alle indsamlede data
        rows = []
        for f in all_features:
            props = f['properties']
            rows.append({
                'Tidspunkt': props['observed'],
                'Parameter': props['parameterId'],
                'Værdi': props['value'],
                'Station': props['stationId']
            })
            
        df = pd.DataFrame(rows)
        df['Tidspunkt'] = pd.to_datetime(df['Tidspunkt'])
        return df.sort_values('Tidspunkt')

    except Exception as e:
        st.error(f"Fejl ved hentning af data: {e}")
        return pd.DataFrame()