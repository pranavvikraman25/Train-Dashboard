import streamlit as st
import json
import folium
from streamlit_folium import st_folium

# Streamlit page setup
st.set_page_config(page_title="TrainSafe — Indian Railways", layout="wide")

st.title("🚄 TrainSafe — Real-Time Railway Collision Prevention System")
st.markdown("### Chennai Central – Perambur Line | Short Route Demo")

# Load the demo GeoJSON route
try:
    with open("frontend/chennai_perambur_demo.geojson", "r") as f:
        route_data = json.load(f)
except FileNotFoundError:
    st.error("❌ GeoJSON file not found! Please upload 'frontend/chennai_perambur_demo.geojson'.")
    st.stop()

# Create Folium map centered around Chennai
m = folium.Map(location=[13.09, 80.26], zoom_start=13, tiles="cartodb positron")

# Add railway route
folium.GeoJson(
    route_data,
    name="Chennai–Perambur Route",
    tooltip="Railway Line: Chennai Central → Perambur",
    style_function=lambda x: {"color": "blue", "weight": 4},
).add_to(m)

# Example trains (demo positions for now)
train_a = [13.0839, 80.2750]  # Chennai Central
train_b = [13.1750, 80.1910]  # Perambur end

# Add train markers
folium.Marker(
    train_a,
    tooltip="🚄 Train A — Chennai Express (Departing)",
    icon=folium.Icon(color="green", icon="train", prefix="fa")
).add_to(m)

folium.Marker(
    train_b,
    tooltip="🚉 Train B — Perambur Local (Arriving)",
    icon=folium.Icon(color="red", icon="train", prefix="fa")
).add_to(m)

# Display the Folium map inside Streamlit
st_folium(m, width=1200, height=600)

# Add project information
st.markdown("""
---
### 🔧 Project Info

**TrainSafe** aims to prevent railway accidents by enabling real-time train-to-train communication and live map visualization.

**This demo shows:**
- The real Chennai Central → Perambur track section  
- Two trains shown as static markers  
- Folium & OpenStreetMap integration inside Streamlit  

**Next phase (with Flask backend):**
- Live GPS updates for each train  
- Automatic alerts when two trains share same track  
- Full route expansion to city-to-city level  
""")
