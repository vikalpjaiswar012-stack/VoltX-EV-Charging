import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import requests
import random

# --- 1. PAGE SETUP (Wide Layout for Dashboard) ---
st.set_page_config(page_title="VoltX EV Dashboard", page_icon="⚡", layout="wide")

# --- 2. DUMMY DATA GENERATION ---
data = {
    'Station Name': ['Acura Hub', 'City Center', 'Greenway', 'Tech Park EV', 'Highway Stop 1', 'Mall Hub', 'Airport Fast Charge'],
    'Lat': [12.985, 12.971, 12.990, 12.960, 12.920, 12.935, 13.198],
    'Lon': [77.550, 77.594, 77.570, 77.580, 77.610, 77.625, 77.706],
    'Status': ['Available', 'Occupied', 'Available', 'Available', 'Maintenance', 'Occupied', 'Available'],
    'Charger Type': ['DC Fast', 'AC Slow', 'DC Fast', 'AC Slow', 'DC Fast', 'AC Slow', 'DC Fast'],
    'Power (kW)': [50, 22, 150, 11, 50, 22, 150],
    'Wait Time': ['0 mins', '15 mins', '0 mins', '0 mins', 'Offline', '30 mins', '0 mins'],
    'Rating': [4.8, 3.5, 4.2, 5.0, 3.9, 4.1, 4.9]
}
df = pd.DataFrame(data)

# Dummy User Location (Bengaluru)
user_lat, user_lon = 12.9716, 77.5946

# --- 3. SIDEBAR (GUI Filters) ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3586/3586936.png", width=60) 
    st.title("⚙️ Control Panel")
    
    st.subheader("Quick Filters")
    only_available = st.toggle("🟢 Show Only Available", value=False)
    autocharge = st.toggle("⚡ Autocharge Enabled", value=False)
    
    st.divider()
    
    st.subheader("Hardware Filters")
    charger_type = st.multiselect("Charger Speed", ["AC Slow", "DC Fast"], default=["AC Slow", "DC Fast"])
    min_power = st.slider("Minimum Power (kW)", 0, 150, 20)
    
    st.divider()
    st.info("📍 Your Location: Bengaluru, India\n\n(Using OpenStreetMap Routing)")

# --- FILTERING LOGIC ---
filtered_df = df[df['Charger Type'].isin(charger_type)]
filtered_df = filtered_df[filtered_df['Power (kW)'] >= min_power]
if only_available:
    filtered_df = filtered_df[filtered_df['Status'] == 'Available']

# --- 4. DASHBOARD HEADER & METRICS ---
st.title("🔋 VoltX Command Dashboard")
st.markdown("Monitor real-time EV charging network status, availability, and routing.")

# KPI Metric Cards (Gives the "Dashboard" look)
col1, col2, col3, col4 = st.columns(4)
col1.metric(label="Total Stations in Area", value=len(df), delta="Active Network")
col2.metric(label="Currently Available", value=len(df[df['Status'] == 'Available']), delta="Ready to use", delta_color="normal")
col3.metric(label="Average Power", value=f"{int(filtered_df['Power (kW)'].mean()) if not filtered_df.empty else 0} kW", delta="Network Avg")
col4.metric(label="Active Users", value="1,284", delta="+14% this week")

st.divider()

# --- 5. MAIN GUI TABS ---
tab1, tab2, tab3 = st.tabs(["🗺️ Live Map View", "📊 Analytics & Data", "🛣️ Trip Planner"])

with tab1:
    map_col, list_col = st.columns([2, 1]) # Map takes 2/3 of screen, list takes 1/3
    
    with map_col:
        st.subheader("Real-Time Availability Map")
        # Build Folium Map
        m = folium.Map(location=[user_lat, user_lon], zoom_start=11, tiles="CartoDB positron") # Cleaner map style
        
        # User Pin
        folium.Marker([user_lat, user_lon], popup="You", icon=folium.Icon(color="black", icon="user")).add_to(m)
        
        # Station Pins
        for i, row in filtered_df.iterrows():
            if row['Status'] == 'Available':
                pin_color = "green"
            elif row['Status'] == 'Occupied':
                pin_color = "orange"
            else:
                pin_color = "gray"
                
            popup_html = f"<b>{row['Station Name']}</b><br>Speed: {row['Power (kW)']} kW<br>Wait: {row['Wait Time']}"
            folium.Marker([row['Lat'], row['Lon']], popup=folium.Popup(popup_html, max_width=200), icon=folium.Icon(color=pin_color, icon="bolt", prefix='fa')).add_to(m)
        
        st_folium(m, width="100%", height=500, returned_objects=[])
        
    with list_col:
        st.subheader("Quick Actions")
        # Creating visually appealing cards for the filtered stations
        for i, row in filtered_df.head(4).iterrows():
            with st.container(border=True):
                st.markdown(f"**{row['Station Name']}** ({row['Rating']} ⭐)")
                status_color = "🟢" if row['Status'] == 'Available' else "🟠" if row['Status'] == 'Occupied' else "⚫"
                st.markdown(f"{status_color} {row['Status']} | ⚡ {row['Power (kW)']} kW")
                
                # OpenStreetMap Link
                nav_url = f"https://www.openstreetmap.org/directions?engine=osrm_car&route={user_lat}%2C{user_lon}%3B{row['Lat']}%2C{row['Lon']}"
                st.link_button("🗺️ Navigate (OSM)", nav_url, use_container_width=True)

with tab2:
    st.subheader("Network Analytics")
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        st.markdown("**Charger Type Distribution**")
        type_counts = df['Charger Type'].value_counts()
        st.bar_chart(type_counts, color="#1f77b4")
        
    with chart_col2:
        st.markdown("**Station Status Overview**")
        status_counts = df['Status'].value_counts()
        st.bar_chart(status_counts, color="#ff7f0e")
        
    st.subheader("Raw Data Table")
    st.dataframe(filtered_df, use_container_width=True, hide_index=True)

with tab3:
    st.subheader("Smart Trip Planner")
    st.info("Enter your route to automatically calculate charging stops along the way.")
    col_from, col_to = st.columns(2)
    start_point = col_from.text_input("From", "Bengaluru, KA")
    end_point = col_to.text_input("To", "Mysuru, KA")
    
    if st.button("Generate Route Plan", type="primary"):
        st.success(f"Route calculated from {start_point} to {end_point}! Found 3 fast chargers along the highway.")
        st.progress(100)
