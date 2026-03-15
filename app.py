with col2:
    st.subheader("Nearest Stations")
    
    # 1. Format the user's origin coordinates as a string
    origin_str = f"{user_location[0]},{user_location[1]}"
    
    # 2. Generate the Google Maps URL for every station in our filtered list
    google_maps_links = []
    for index, row in filtered_df.iterrows():
        dest_str = f"{row['Lat']},{row['Lon']}"
        url = f"https://www.google.com/maps/dir/?api=1&origin={origin_str}&destination={dest_str}&travelmode=driving"
        google_maps_links.append(url)
        
    # Add these URLs as a new column in our dataframe
    filtered_df['Navigate Link'] = google_maps_links

    # 3. Display the dataframe using Streamlit's LinkColumn for a clean UI
    st.dataframe(
        filtered_df[['Station Name', 'Distance', 'Driving Time', 'Navigate Link']],
        use_container_width=True,
        hide_index=True, # Hides the row numbers for a cleaner look
        column_config={
            # This turns the ugly URL into a clean, clickable "🗺️ Go" text
            "Navigate Link": st.column_config.LinkColumn(
                "Navigate", 
                display_text="🗺️ Go" 
            )
        }
    )
