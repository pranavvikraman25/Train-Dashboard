import streamlit as st
import json
import time
import math
from geopy.distance import geodesic

st.set_page_config(page_title="Smart Train Safety Dashboard", layout="wide")

st.markdown("## 🚆 Indian Southern Railways Limited")
st.markdown("#### Chennai – Mumbai | Train No: 64521")

# --- Load train data ---
with open("trains_data.json") as f:
    trains = json.load(f)

# Simulation speed (to visualize movement)
refresh_rate = 1  # seconds
speed_factor = 0.03  # control animation step

# Canvas setup
canvas = st.empty()
info_col, status_col = st.columns([2, 1])

def calc_distance(a, b):
    return geodesic((a["lat"], a["lon"]), (b["lat"], b["lon"])).km

def meeting_time(dist, s1, s2):
    avg_speed = (s1 + s2) / 2
    return round(dist / avg_speed * 60, 2) if avg_speed > 0 else 0

# --- Layout Drawing ---
def draw_dashboard(trains):
    with canvas.container():
        st.markdown("---")
        st.write("#### 🚉 Track Overview (Top View)")
        st.write("")
        st.write("Track 1 | ---------------------- 🚆" if trains["Train_1"]["moving"] else "Track 1 | 🚦 STOP 🚆")
        st.write("Track 2 | ---------------------- 🚆" if trains["Train_2"]["moving"] else "Track 2 | 🚦 STOP 🚆")
        st.write("Track 3 | ---------------------- ")
        st.write("Track 4 | ---------------------- ")
        st.markdown("---")

    with info_col:
        st.markdown("### 🧭 Live Train Details")
        for name, t in trains.items():
            st.write(f"**{name}** — {t['route']}")
            st.write(f"📍 Distance Away: {t['distance']} km | 🛤 Track: {t['track']}")
            if t["moving"]:
                st.success(f"💨 Speed: {t['speed']} km/h | ETA: {t['eta']} mins")
            else:
                st.error("🚦 Waiting for Clearance")
            st.markdown("---")

    with status_col:
        st.markdown("### ⚙️ System Status")
        st.write(f"Current Time: {time.strftime('%H:%M:%S')}")
        st.write("Active Trains: ", len(trains))
        st.write("Track Health: ✅ Stable")
        st.markdown("---")

# --- Core Logic ---
while True:
    # Compute distances
    dist = calc_distance(trains["Train_1"], trains["Train_2"])
    eta = meeting_time(dist, trains["Train_1"]["speed"], trains["Train_2"]["speed"])

    # Decision logic
    if dist < 10 and trains["Train_1"]["track"] == trains["Train_2"]["track"]:
        trains["Train_1"]["moving"] = False
        trains["Train_2"]["moving"] = True
        msg = "🚨 ALERT: Trains too close — Train 1 halted to let Train 2 cross!"
    else:
        trains["Train_1"]["moving"] = True
        trains["Train_2"]["moving"] = True
        msg = "✅ Safe — Trains operating normally."

    for t in trains.values():
        t["eta"] = eta
        if t["moving"]:
            t["distance"] = max(0, t["distance"] - (t["speed"] * speed_factor))
        else:
            t["speed"] = 0

    st.info(msg)
    draw_dashboard(trains)
    time.sleep(refresh_rate)
