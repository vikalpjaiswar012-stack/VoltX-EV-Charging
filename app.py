import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import googlemaps

# --- 1. PAGE SETUP ---
st.set_page_config(page_title="VoltX EV App", page_icon="⚡", layout="wide")

# Initialize Google Maps API securely
try:
    gmaps = googlemaps.Client(key=st.secrets["GOOGLE_MAPS_API_KEY"])
    api_ready = True
except Exception:
    api_ready = False

# --- 2. DUMMY STATION DATA ---
data = {
    'Station Name': ['VoltX Acura Hub', 'City Center Fast Charge', 'Greenway Station', 'Tech Park EV', 'Highway Stop 1'],
    'Lat': [12.985, 12.971, 12.990, 12.960, 12.920],
    'Lon': [77.550, 77.594, 77.570, 77.580, 77.610],
    'Available': [True, False, True, True, False],
    'Charger Type': ['DC', 'AC', 'DC', 'AC', 'DC'],
    'Wait Time': ['Now', '15 Mins', 'Now', 'Now', '45 Mins'],
    'Rating': [4.8, 3.5, 4.2, 5.0, 3.9]
}
df = pd.DataFrame(data)

# --- 3. SIDEBAR DASHBOARD ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3586/3586936.png", width=50) # Generic EV icon
st.sidebar.title("⚡ VoltX Filters")

user_loc_input = st.sidebar.text_input("📍 Your Location", "Bengaluru, India")
only_available = st.sidebar.toggle("Only available chargers", value=False)
autocharge = st.sidebar.toggle("Autocharge Support", value=False)

st.sidebar.divider()
charger_type = st.sidebar.multiselect("Charger Type", ["AC", "DC"], default=["AC", "DC"])

# Filter Logic
filtered_df = df[df['Charger Type'].isin(charger_type)]
if only_available:
    filtered_df = filtered_df[filtered_df['Available'] == True]

# --- 4. CALCULATE DISTANCES (Google Maps) ---
distances, durations, nav_links = [], [], []

for index, row in filtered_df.iterrows():
    dest_str = f"{row['Lat']},{row['Lon']}"
    
    if api_ready:
        try:
            result = gmaps.distance_matrix(origins=user_loc_input, destinations=dest_str, mode="driving")
            dist_text = result['rows'][0]['elements'][0]['distance']['text']
            dur_text = result['rows'][0]['elements'][0]['duration']['text']
        except:
            dist_text, dur_text = "Est. 5 km", "Est. 15 mins"
    else:
        dist_text, dur_text = "API Key Needed", "API Key Needed"
        
    distances.append(dist_text)
    durations.append(dur_text)
    
    # Generate Google Maps Navigation Link
    url = f"https://www.google.com/maps/dir/?api=1&origin={user_loc_input}&destination={dest_str}&travelmode=driving"
    nav_links.append(url)

filtered_df['Distance'] = distances
filtered_df['Driving Time'] = durations
filtered_df['Navigate Link'] = nav_links

# --- 5. MAIN UI ---
st.title("🔋 VoltX EV Station Locator")
if not api_ready:
    st.warning("⚠️ Google Maps API Key missing in Streamlit Secrets. Distances are estimated.")

tab1, tab2, tab3 = st.tabs(["🗺️ Station Map", "🛣️ Trip Planner", "📍 Generate Lead"])

with tab1:
    col1, col2 = st.columns([2, 1])
    with col1:
        # Default map center
        m = folium.Map(location=[12.9716, 77.5946], zoom_start=12)
        
        for i, row in filtered_df.iterrows():
            color = "green" if row['Available'] else "red"
            popup_html = f"<b>{row['Station Name']}</b><br>Wait: {row['Wait Time']}<br>Type: {row['Charger Type']}"
            folium.Marker([row['Lat'], row['Lon']], popup=folium.Popup(popup_html, max_width=200), icon=folium.Icon(color=color, icon="bolt", prefix='fa')).add_to(m)
        
        st_folium(m, width=700, height=500)
        
    with col2:
        st.subheader("Nearest Stations")
        st.dataframe(
            filtered_df[['Station Name', 'Wait Time', 'Distance', 'Navigate Link']],
            use_container_width=True, hide_index=True,
            column_config={"Navigate Link": st.column_config.LinkColumn("Navigate", display_text="🗺️ Go")}
        )

with tab2:
    st.subheader("Smart Trip Planner")
    colA, colB = st.columns(2)
    start = colA.text_input("Starting Point", "Bengaluru")
    end = colB.text_input("Destination", "Mysuru")
    st.button("Calculate Route & Charging Stops", type="primary")

with tab3:
    st.subheader("Crowdsource: Generate Lead")
    st.text_input("Location Name (e.g., Mall Parking Lot)")
    st.text_area("Why is this a good spot for a fast charger?")
    st.button("Submit Lead", type="primary")
