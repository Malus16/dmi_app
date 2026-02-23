# DMI Weather Web App

A [Streamlit](https://streamlit.io/) web application that makes data from the Danish Meteorological Institute's (DMI) API easily accessible, visual, and useful.

🔗 **Live App:** [dmi-data.streamlit.app](https://dmi-data.streamlit.app)

## Features

### Currently Available:
- **Station & Parameter Selection:** Choose between various predefined Danish weather stations and fetch specific meteorological parameters (e.g., Temperature, Wind Speed, Precipitation, Humidity).
- **Custom Time Ranges:** Select a custom date range to fetch historical data for. Time ranges are automatically constrained based on when the specific station started recording data for the chosen parameter.
- **Data Visualization:** Interactive Plotly line charts visualizing the fetched data over time.
- **CSV Export:** Download the precise data you are viewing directly as a `.csv` file for external analysis.
- **Historical Statistics & Records:** (WIP) A unified view of historical extremes (highest/lowest temperatures, max wind speeds, etc.) and average monthly climate normals for the selected station, generated from a local SQLite database of aggregated daily values.
- **Historical Period Comparison:** (WIP) Compare aggregated statistics (Minimum, Maximum, Average) across all available years for a specific time of year (e.g., "Marts 1. to Marts 7.").

### Future Plans:
- **Full Historical Coverage:** Flesh out the local SQLite database to include full historical aggregated statistics for *all* DMI stations.
- **Geographical Station Map:** A visual map interface to discover and select weather stations based on location rather than a dropdown list.
- **Advanced Historical Statistics:** Deeper analytical insights from decades of weather records.
- **Forecast Dashboards / "Heads-Up":** Introducing near-future forecast data to monitor upcoming extremes (e.g., a dashboard highlighting "These 3 stations might break their coldest temperature record tonight!").

## Running Locally

1. Clone this repository.
2. Install the required Python packages (Streamlit, Pandas, Plotly, Requests).
3. Run the app:
   ```bash
   streamlit run app.py
   ```
