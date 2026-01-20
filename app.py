import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# --- Konfiguration ---
API_BASE = "https://opendataapi.dmi.dk/v2/metObs/collections/observation/items"

# Parameter-liste (Dansk)
PARAMS = {
    "Temperatur (tør)": "temp_dry",
    "Nedbør (sidste time)": "precip_past1h",
    "Vindhastighed": "wind_speed",
    "Luftfugtighed": "humidity",
    "Lufttryk": "pressure",
    "Solskinstimer": "sun_last1h_glob"
}

# Stationer (Navn -> ID)
STATIONS = {
    "Københavns Lufthavn (Kastrup)": "06180",
    "Aarhus Syd": "06071",
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

# def fetch_dmi_data(station_id, param_id, start_date, end_date):
#     # Formater datoer til RFC3339
#     time_str = f"{start_date.isoformat()}T00:00:00Z/{end_date.isoformat()}T23:59:59Z"
    
#     params = {
#         'parameterId': param_id,
#         'stationId': station_id,
#         'datetime': time_str,
#         'limit': 1000, 
#         'api-key': ''   
#     }
    
#     try:
#         response = requests.get(API_BASE, params=params)
#         response.raise_for_status()
#         data = response.json()
        
#         features = data.get('features', [])
#         if not features:
#             return pd.DataFrame()
            
#         rows = []
#         for f in features:
#             props = f['properties']
#             rows.append({
#                 'Tidspunkt': props['observed'],
#                 'Parameter': props['parameterId'],
#                 'Værdi': props['value'],
#                 'Station': props['stationId']
#             })
            
#         df = pd.DataFrame(rows)
#         df['Tidspunkt'] = pd.to_datetime(df['Tidspunkt'])
#         return df.sort_values('Tidspunkt')

#     except Exception as e:
#         st.error(f"Fejl ved hentning af data: {e}")
#         return pd.DataFrame()

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
    
    # Placeholder til statusbesked på skærmen
    status_text = st.empty()
    
    try:
        while True:
            # Opdater offset for at hente næste side
            params['offset'] = offset
            
            # Vis brugeren at vi arbejder
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
    
# --- UI Layout ---
st.title("DMI Vejrdata Downloader")

with st.sidebar:
    st.header("Indstillinger")
    
    # NYT: Dropdown til stationer
    selected_station_name = st.selectbox("Vælg Station", list(STATIONS.keys()))
    station_id = STATIONS[selected_station_name] # Slå ID op baseret på navnet
    
    st.caption(f"Stations ID: {station_id}") # Viser ID'et til brugeren for info

    selected_param_name = st.selectbox("Parameter", list(PARAMS.keys()))
    
    min_date_limit = datetime(2011, 1, 1)
    max_date_limit = datetime.now()
    col1, col2 = st.columns(2)
    # start_d = col1.date_input("Startdato", datetime.now() - timedelta(days=2))
    # end_d = col2.date_input("Slutdato", datetime.now() - timedelta(days=1))
    start_d = col1.date_input(
        "Startdato", 
        value=max_date_limit - timedelta(days=1),
        min_value=min_date_limit,                   # Låser bagud til 2011
        max_value=max_date_limit                    # Låser fremad til i dag
    )
    
    end_d = col2.date_input(
        "Slutdato", 
        value=max_date_limit,
        min_value=min_date_limit,
        max_value=max_date_limit
    )

    fetch_btn = st.button("Hent Data")

if fetch_btn:
    param_id = PARAMS[selected_param_name]
    
    with st.spinner(f"Henter {selected_param_name} fra {selected_station_name}..."):
        df = fetch_dmi_data(station_id, param_id, start_d, end_d)
    
    if not df.empty:
        # Plot
        st.subheader(f"Graf: {selected_param_name}")
        fig = px.line(df, x='Tidspunkt', y='Værdi', title=f"{selected_param_name} - {selected_station_name}")
        
        fig.update_layout(xaxis_title="Tid", yaxis_title=selected_param_name)
        st.plotly_chart(fig, width='stretch')
        
        # Tabel
        st.subheader("Dataoversigt")
        st.dataframe(df.head())
        
        # Download
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download CSV fil",
            data=csv,
            file_name=f"dmi_{param_id}_{station_id}.csv",
            mime="text/csv"
        )
    else:
        st.warning("Ingen data fundet. Prøv en anden parameter eller dato.")