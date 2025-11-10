import streamlit as st
import json
import pandas as pd
from utils.functions import calculate_distance, calculate_eta, get_status
from streamlit_folium import st_folium
import folium

st.set_page_config(page_title="Smart Train Communication", layout="wide")
st.title("🚆 Smart Train-to-Train Communication Dashboard")

# Load JSON data
with open("data/train_data.json") as f:
    trains = json.load(f)

# Display map
m = folium.Map(location=[13.0, 80.2], zoom_start=8)
for name, train in trains.items():
    color = "red" if train["signal"] == 0 else "green"
    folium.Marker(
        [train["lat"], train["lon"]],
        popup=f"{name} | Speed: {train['speed']} km/h",
        icon=folium.Icon(color=color)
    ).add_to(m)

st_folium(m, width=700, height=500)

# Dashboard info
st.subheader("📍 Live Train Data")
for name, train in trains.items():
    status = get_status(train)
    st.write(f"**{name}** — {status}")
    st.write(f"🧭 Coordinates: ({train['lat']}, {train['lon']})")
    st.write(f"⚡ Speed: {train['speed']} km/h")
    st.divider()

# Safety alert section
st.subheader("⚠️ Collision Alerts")

train_names = list(trains.keys())
for i in range(len(train_names)):
    for j in range(i + 1, len(train_names)):
        t1, t2 = train_names[i], train_names[j]
        dist = calculate_distance(trains[t1], trains[t2])
        st.write(f"🧩 Distance between {t1} and {t2}: **{dist:.2f} km**")

        if dist < 40:
            eta = calculate_eta(dist, (trains[t1]["speed"] + trains[t2]["speed"]) / 2)
            st.error(f"🚨 ALERT: {t1} and {t2} are within 40 km!")
            if eta:
                st.warning(f"⏱ Estimated Meeting Time: {eta} mins")
        else:
            st.success(f"✅ Safe distance maintained.")
