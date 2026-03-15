import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import requests

# --- 1. PAGE SETUP ---
st.set_page_config(page_title="VoltX EV App", page_icon="⚡", layout="wide")

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
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3586/3586936.png", width=50) 
st.sidebar.title("⚡ VoltX Filters")

# Using coordinates for user location (Bengaluru center)
user_lat = 12.9716
user_lon = 77.5946
st.sidebar.write("📍 **Your Location:** Bengaluru (Dummy GPS)")

only_available = st.sidebar.toggle("Only available chargers", value=False)
autocharge = st.sidebar.toggle("Autocharge Support", value=False)

st.sidebar.divider()
charger_type = st.sidebar.multiselect("Charger Type", ["AC", "DC"], default=["AC", "DC"])

# Filter Logic
filtered_df = df[df['Charger Type'].isin(charger_type)]
if only_available:
    filtered_df = filtered_df[filtered_df['Available'] == True]

# --- 4. CALCULATE DISTANCES (Open Source OSRM) ---
distances, durations, nav_links = [], [], []

for index, row in filtered_df.iterrows():
    # OSRM API expects format: {longitude},{latitude}
    osrm_url = f"http://router.project-osrm.org/route/v1/driving/{user_lon},{user_lat};{row['Lon']},{row['Lat']}?overview=false"
    
    try:
        response = requests.get(osrm_url).json()
        if response.get("code") == "Ok":
            # Convert meters to km
            dist_km = round(response['routes'][0]['distance'] / 1000, 1)
            # Convert seconds to minutes
            dur_min = round(response['routes'][0]['duration'] / 60)
            
            dist_text = f"{dist_km} km"
            dur_text = f"{dur_min} mins"
        else:
            dist_text, dur_text = "N/A", "N/A"
    except:
        dist_text, dur_text = "Error", "Error"
        
    distances.append(dist_text)
    durations.append(dur_text)
    
    # Generate OpenStreetMap Navigation Link
    osm_nav_link = f"https://www.openstreetmap.org/directions?engine=osrm_car&route={user_lat}%2C{user_lon}%3B{row['Lat']}%2C{row['Lon']}"
    nav_links.append(osm_nav_link)

filtered_df['Distance'] = distances
filtered_df['Driving Time'] = durations
filtered_df['Navigate Link'] = nav_links

# --- 5. MAIN UI ---
st.title("🔋 VoltX EV Station Locator")
st.success("🌍 Powered entirely by OpenStreetMap and OSRM (No API Key Required!)")

tab1, tab2, tab3 = st.tabs(["🗺️ Station Map", "🛣️ Trip Planner", "📍 Generate Lead"])

with tab1:
    col1, col2 = st.columns([2, 1])
    with col1:
        # Default map center (Folium inherently uses OpenStreetMap)
        m = folium.Map(location=[user_lat, user_lon], zoom_start=12)
        
        # Add user location pin
        folium.Marker([user_lat, user_lon], popup="You are here", icon=folium.Icon(color="blue", icon="user")).add_to(m)
        
        # Add station pins
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
