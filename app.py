import streamlit as st
import folium
import osmnx as ox
from streamlit_folium import st_folium
from geopy.distance import geodesic
import time
import pandas as pd

st.set_page_config(page_title="TrainSafe Real Route", layout="wide")
st.title("🚆 Smart Train Safety Dashboard — Indian Southern Railways")
st.markdown("**Route Demo:** Chennai – Bangalore | Real OSM Railway Route**")

# --- 1. Load route only once ---
if "rail_route" not in st.session_state:
    with st.spinner("Fetching real railway data from OpenStreetMap..."):
        # Fetch railway track between Chennai and Bangalore
        G = ox.graph_from_place("Tamil Nadu, India", network_type="all")
        edges = ox.graph_to_gdfs(G, nodes=False)
        rail_edges = edges[edges["railway"].notnull()]
        # Filter roughly along Chennai–Bangalore region
        route = rail_edges[(rail_edges["geometry"].bounds.minx > 77.5) & (rail_edges["geometry"].bounds.maxx < 80.5)]
        st.session_state.rail_route = route
        st.session_state.base_map = folium.Map(location=[12.95, 79.95], zoom_start=8, tiles="OpenStreetMap")
        for _, row in route.iterrows():
            folium.PolyLine(
                locations=[(pt[1], pt[0]) for pt in row["geometry"].coords],
                color="gray", weight=2, opacity=0.7
            ).add_to(st.session_state.base_map)

# --- 2. Train initial data ---
if "train_data" not in st.session_state:
    st.session_state.train_data = pd.DataFrame([
        {"name": "Train_1", "route": "Chennai–Bangalore", "lat": 13.0827, "lon": 80.2707, "speed": 85, "track": 2},
        {"name": "Train_2", "route": "Kovai–Madurai", "lat": 12.9827, "lon": 80.0707, "speed": 75, "track": 1}
    ])

# --- 3. Simulation control ---
cols = st.columns([1, 1, 3])
start = cols[0].button("▶ Start")
stop = cols[1].button("■ Stop")
reset = cols[2].button("↺ Reset")

if "running" not in st.session_state:
    st.session_state.running = False
if start:
    st.session_state.running = True
if stop:
    st.session_state.running = False
if reset:
    st.session_state.train_data.loc[0, ["lat", "lon"]] = [13.0827, 80.2707]
    st.session_state.train_data.loc[1, ["lat", "lon"]] = [12.9827, 80.0707]
    st.session_state.running = False

# --- 4. Display persistent map ---
with st.container():
    map_placeholder = st.empty()
    m = st.session_state.base_map

    # Add markers for current positions
    for _, row in st.session_state.train_data.iterrows():
        folium.Marker(
            location=[row["lat"], row["lon"]],
            popup=f"{row['name']} ({row['route']})<br>Speed: {row['speed']} km/h",
            icon=folium.Icon(color="red" if row["speed"] == 0 else "green", icon="train", prefix="fa")
        ).add_to(m)

    st_folium(m, width=950, height=600, key="live_map")

# --- 5. Logic to move trains on same map ---
def move_train(lat, lon, dest_lat, dest_lon, step_km):
    dist = geodesic((lat, lon), (dest_lat, dest_lon)).km
    if dist == 0 or step_km >= dist:
        return dest_lat, dest_lon
    frac = step_km / dist
    new_lat = lat + (dest_lat - lat) * frac
    new_lon = lon + (dest_lon - lon) * frac
    return new_lat, new_lon

# --- 6. Update simulation ---
if st.session_state.running:
    for i in range(100):  # limited steps
        # Move train 1 north-west (towards Bangalore approx)
        t1 = st.session_state.train_data.loc[0]
        new_lat, new_lon = move_train(t1["lat"], t1["lon"], 12.97, 77.59, t1["speed"] * 0.001)
        st.session_state.train_data.loc[0, ["lat", "lon"]] = [new_lat, new_lon]

        # Move train 2 slightly south (simulate crossing)
        t2 = st.session_state.train_data.loc[1]
        new_lat2, new_lon2 = move_train(t2["lat"], t2["lon"], 9.92, 78.12, t2["speed"] * 0.001)
        st.session_state.train_data.loc[1, ["lat", "lon"]] = [new_lat2, new_lon2]

        # Safety check
        dist = geodesic((new_lat, new_lon), (new_lat2, new_lon2)).km
        if dist < 10:
            st.warning(f"🚨 Collision risk: {t1['name']} & {t2['name']} within {dist:.2f} km!")
            st.session_state.train_data.loc[0, "speed"] = 0
        else:
            st.success(f"✅ Safe operation — distance: {dist:.2f} km")

        time.sleep(0.8)
        st.experimental_rerun()
