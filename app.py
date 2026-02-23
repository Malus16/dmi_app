import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

from modules import dmi_client, database
    
# --- UI Layout ---

st.title("DMI Vejrdata Downloader")

with st.sidebar:
    st.header("Indstillinger")

    selected_station_name = st.selectbox("Vælg Station", list(dmi_client.STATIONS.keys()))
    station_id = dmi_client.STATIONS[selected_station_name] # Slå ID op baseret på navnet
    
    st.caption(f"Stations ID: {station_id}") # Viser ID'et til brugeren for info

    selected_param_name = st.selectbox("Parameter", list(dmi_client.PARAMS.keys()))
    
    min_date_limit = datetime(1958, 1, 1)
    max_date_limit = datetime.now()
    col1, col2 = st.columns(2)

    start_d = col1.date_input(
        "Startdato", 
        value=max_date_limit - timedelta(days=365),
        min_value=min_date_limit, # Låser bagud
        max_value=max_date_limit  # Låser fremad
    )
    
    end_d = col2.date_input(
        "Slutdato", 
        value=max_date_limit,
        min_value=min_date_limit,
        max_value=max_date_limit
    )

    fetch_btn = st.button("Hent Data")

# Initialize state if it doesn't exist
if 'data' not in st.session_state:
    st.session_state['data'] = None

# If the button is clicked, we fetch NEW data and save it to state
if fetch_btn:
    param_id = dmi_client.PARAMS[selected_param_name]
    
    with st.spinner(f"Henter {selected_param_name} fra {selected_station_name}..."):
        # We save the result directly into session_state
        st.session_state['data'] = dmi_client.fetch_dmi_data(station_id, param_id, start_d, end_d)
        st.session_state['current_param'] = selected_param_name
        st.session_state['current_station'] = station_id
        st.session_state['current_station_name'] = selected_station_name

# Now we check if we HAVE data in the state (regardless of button click)
if st.session_state['data'] is not None and not st.session_state['data'].empty:
    
    # Reload variables from state to ensure consistency
    df = st.session_state['data']
    curr_param = st.session_state['current_param']
    curr_stat_id = st.session_state['current_station']
    curr_stat_name = st.session_state['current_station_name']

    # --- 1. PLOTTING ---
    st.subheader(f"Graf: {curr_param}")
    fig = px.line(df, x='Tidspunkt', y='Værdi', title=f"{curr_param} - {curr_stat_name}")
    fig.update_layout(xaxis_title="Tid", yaxis_title=curr_param)
    st.plotly_chart(fig, use_container_width=True)
    
    # --- 2. DOWNLOAD ---
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download CSV fil",
        data=csv,
        file_name=f"dmi_{curr_stat_id}.csv",
        mime="text/csv"
    )

    # --- 3. FUN FACTS ---
    st.markdown("---")
    st.header("🏆 Rekorder & Statistik (Fra tidligste datapunkt)")
    
    import os
    if not os.path.exists("dmi_stats.db"):
        st.warning("⚠️ Database ikke fundet.")
    else:
        extremes = database.get_station_extremes(curr_stat_id)
        
        c1, c2, c3 = st.columns(3)
        
        # Max Temp
        with c1:
            rec = extremes['max_temp']
            if rec is not None:
                date_str = pd.to_datetime(rec['observed_at']).strftime("%d %b %Y")
                st.metric("Højeste Temp", f"{rec['value']} °C", f"{date_str}")
            else:
                st.metric("Højeste Temp", "-")
                
        # Min Temp
        with c2:
            rec = extremes['min_temp']
            if rec is not None:
                date_str = pd.to_datetime(rec['observed_at']).strftime("%d %b %Y")
                st.metric("Laveste Temp", f"{rec['value']} °C", f"{date_str}")
            else:
                st.metric("Laveste Temp", "-")

        # Max Wind
        with c3:
            rec = extremes['max_wind']
            if rec is not None:
                date_str = pd.to_datetime(rec['observed_at']).strftime("%d %b %Y")
                st.metric("Højeste middelvind", f"{rec['value']} m/s", f"{date_str}")
            else:
                st.metric("Højeste middelvind", "-")

        st.markdown("---")
        
        # Monthly Averages
        st.subheader("📅 Månedlig Klimanormal (Fra tidligste datapunkt)")
        
        months = {
            1: "Januar", 2: "Februar", 3: "Marts", 4: "April",
            5: "Maj", 6: "Juni", 7: "Juli", 8: "August",
            9: "September", 10: "Oktober", 11: "November", 12: "December"
        }
        
        current_month_idx = datetime.now().month
        selected_month_name = st.selectbox(
            "Vælg en måned:", 
            list(months.values()), 
            index=current_month_idx - 1 
        )
        
        # Find ID for selected month
        name_to_id = {v: k for k, v in months.items()}
        selected_month_id = name_to_id[selected_month_name]
        
        # This will now run without clearing the graph above
        avg_val = database.get_monthly_average(curr_stat_id, selected_month_id)
        
        if avg_val is not None:
            st.info(f"Gennemsnittet for **{selected_month_name}** er **{avg_val:.1f} °C**.")
        else:
            st.warning(f"Ingen data for {selected_month_name}.")
            
elif fetch_btn: # Only triggers if we clicked button but got no data
    st.warning("Ingen data fundet.")