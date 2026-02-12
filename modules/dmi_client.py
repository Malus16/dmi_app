import requests
import pandas as pd
import streamlit as st 

API_BASE = "https://opendataapi.dmi.dk/v2/metObs/collections/observation/items"

# Parameter-liste (Dansk)
PARAMS = {
    "Temperatur (tør)": "temp_dry",
    "Nedbør (sidste time)": "precip_past1h",
    "Vindhastighed": "wind_speed",  
    "Luftfugtighed": "humidity",
    "Lufttryk": "pressure",
    "Solskinstimer": "sun_last1h_glob",
    "Sigtbarhed": "visibility"
}

# Stationer (Navn -> ID)
STATIONS = {
    "Københavns Lufthavn (Kastrup)": "06180",
    "Ødum": "06072",
    "Odense Lufthavn": "06120",
    "Aalborg Lufthavn": "06030",
    "Esbjerg Lufthavn": "06060",
    "Roskilde Lufthavn": "06135",
    "Rønne (Bornholm)": "06190",
    "Skagen Fyr": "06041",
    "Sønderborg Lufthavn": "06110",
    "Karup (Midtjylland)": "06068",
    "Hammer Odde Fyr": "06193"
}

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