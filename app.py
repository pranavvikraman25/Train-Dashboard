import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from geopy.distance import geodesic
import time
import math

# Streamlit page config
st.set_page_config(page_title="TrainSafe Live Dashboard", layout="wide")

st.title("🚆 TrainSafe Live System – Indian Southern Railways")
st.markdown("**Train No: 64521 | Chennai – Mumbai**")

# --- Load Train Data ---
data = pd.DataFrame([
    {"name": "Train 1", "route": "Chennai–Bangalore", "lat": 13.0827, "lon": 80.2707, "speed": 85, "track": 2},
    {"name": "Train 2", "route": "Kovai–Madurai", "lat": 12.9827, "lon": 80.0707, "speed": 0, "track": 1},
    {"name": "Train 3", "route": "Chennai–Mumbai", "lat": 13.5, "lon": 79.8, "speed": 90, "track": 3}
])

# --- Setup Map ---
m = folium.Map(location=[13.0, 80.1], zoom_start=8, tiles="OpenStreetMap")

# Add tracks (simple colored polylines)
track_colors = {1: "blue", 2: "red", 3: "green", 4: "orange"}
for t in range(1, 5):
    lat_shift = 0.05 * (t - 2)  # separate tracks slightly
    folium.PolyLine(
        [(12.5 + lat_shift, 79.7), (13.5 + lat_shift, 80.3)],
        color=track_colors[t], weight=3, opacity=0.7, tooltip=f"Track {t}"
    ).add_to(m)

# --- Add Trains ---
for _, row in data.iterrows():
    folium.Marker(
        location=[row["lat"], row["lon"]],
        popup=f"{row['name']} ({row['route']})<br>Speed: {row['speed']} km/h<br>Track: {row['track']}",
        icon=folium.Icon(color="red" if row["speed"] == 0 else "green", icon="train", prefix="fa")
    ).add_to(m)

# Display map
st_folium(m, width=1000, height=550)

# --- Alerts and Data Section ---
st.subheader("📡 Live Train Information")
for i, row in data.iterrows():
    status = "🟥 STOPPED" if row["speed"] == 0 else "🟩 MOVING"
    st.write(f"**{row['name']}** — {row['route']} | {status} | Track {row['track']} | {row['speed']} km/h")

# --- Simple Collision Check ---
train1 = data.iloc[0]
train2 = data.iloc[1]
dist = geodesic((train1["lat"], train1["lon"]), (train2["lat"], train2["lon"])).km

if dist < 10 and train1["track"] == train2["track"]:
    st.error(f"🚨 ALERT: {train1['name']} and {train2['name']} are within {dist:.1f} km on the same track!")
else:
    st.success(f"✅ Safe distance between trains: {dist:.1f} km")

st.caption(f"🕒 Last updated: {time.strftime('%H:%M:%S')} | Data simulated from OSM route paths")
