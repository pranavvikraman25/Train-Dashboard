# app.py
import streamlit as st
import json
import time
from math import radians, degrees, sin, cos, atan2
from geopy.distance import geodesic
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="TrainSafe Live — Demo", layout="wide")

# ---------- Helpers ----------
def load_trains(path="trains_data.json"):
    with open(path, "r") as f:
        return json.load(f)

def save_trains(trains, path="trains_data.json"):
    with open(path, "w") as f:
        json.dump(trains, f, indent=2)

def distance_km(a_lat, a_lon, b_lat, b_lon):
    return geodesic((a_lat, a_lon), (b_lat, b_lon)).km

def bearing_deg(a_lat, a_lon, b_lat, b_lon):
    # Bearing from point A to B in degrees (0..360)
    lat1, lon1, lat2, lon2 = map(radians, [a_lat, a_lon, b_lat, b_lon])
    dlon = lon2 - lon1
    x = sin(dlon) * cos(lat2)
    y = cos(lat1) * sin(lat2) - sin(lat1) * cos(lat2) * cos(dlon)
    brng = atan2(x, y)
    brng = degrees(brng)
    return (brng + 360) % 360

def dest_point(lat, lon, brng_deg, dist_km):
    # Move from lat,lon by dist_km in direction brng_deg -> return new lat/lon
    # Using a simple spherical formula (sufficient for short demo steps)
    R = 6371.0  # Earth radius km
    brng = radians(brng_deg)
    lat1 = radians(lat)
    lon1 = radians(lon)
    lat2 = asin = None
    lat2 = sin(lat1)*cos(dist_km/R) + cos(lat1)*sin(dist_km/R)*cos(brng)
    # clamp in case of fp issues
    if lat2 > 1: lat2 = 1
    if lat2 < -1: lat2 = -1
    lat2 = atan2(sin(lat1)*cos(dist_km/R) + cos(lat1)*sin(dist_km/R)*cos(brng),
                 (1e-12 + cos(lat1)*cos(dist_km/R) - sin(lat1)*sin(dist_km/R)*cos(brng)))
    lon2 = lon1 + atan2(sin(brng)*sin(dist_km/R)*cos(lat1),
                        cos(dist_km/R)-sin(lat1)*sin(lat2))
    return degrees(lat2), ((degrees(lon2)+540) % 360) - 180

# simpler safe destination using geopy (less math headaches)
from geopy.distance import distance as geopy_distance
def move_towards(lat, lon, lat_to, lon_to, step_km):
    """Return new lat, lon moved from (lat,lon) towards (lat_to,lon_to) by step_km (or directly lat_to when step>=dist)."""
    dist = distance_km(lat, lon, lat_to, lon_to)
    if dist == 0 or step_km <= 0:
        return lat, lon
    if step_km >= dist:
        return lat_to, lon_to
    # fraction to move
    frac = step_km / dist
    # linear interpolation in lat/lon (fine for short steps)
    new_lat = lat + (lat_to - lat) * frac
    new_lon = lon + (lon_to - lon) * frac
    return new_lat, new_lon

# ---------- Streamlit UI ----------
st.title("🚆 TrainSafe Live — Demo (OpenStreetMap)")
st.markdown("**Animated train movement, same-track conflict detection and ETA**")

# Controls
cols = st.columns([1, 1, 2, 1])
start_btn = cols[0].button("▶ Start Simulation")
stop_btn = cols[1].button("■ Stop Simulation")
reset_btn = cols[2].button("↺ Reset positions")
speed_input = cols[3].slider("Sim speed (x)", 1, 10, 3)

# Load base data
trains = load_trains()

# Option to set a target for each train for demo purposes.
# For demo, keep simple: set each train's "target" as a nearby point in same direction.
# If trains.json has no target, give them a default target.
for t in trains.values():
    if "target" not in t:
        # Small offset to show motion
        t["target"] = {"lat": t["lat"] + 0.3, "lon": t["lon"] + 0.2}
    if "stopped" not in t:
        t["stopped"] = False
    if "distance" not in t:
        t["distance"] = round(distance_km(t["lat"], t["lon"], t["target"]["lat"], t["target"]["lon"]), 2)

# placeholder containers (these will be overwritten each frame)
map_placeholder = st.empty()
left_placeholder = st.empty()
alert_placeholder = st.empty()

# logic parameters
FRAME_SECONDS = 1.0  # seconds per frame (rough)
MAX_FRAMES = 200     # maximum frames for demo loop
STOP_THRESHOLD_KM = 10.0  # when two trains same track within this km, stop one
# choose which train yields when conflict: simple rule train with larger distance yields (or train with lower priority)
def decide_yield(t1, t2):
    # return name of train that should stop (t1 or t2)
    if t1["distance"] > t2["distance"]:
        return t1["name"]
    return t2["name"]

# prevent multi-run: store simulation flag in session_state
if "running" not in st.session_state:
    st.session_state.running = False
if start_btn:
    st.session_state.running = True
if stop_btn:
    st.session_state.running = False
if reset_btn:
    # reset positions to initial values saved in JSON file (we simply reload)
    trains = load_trains()
    for t in trains.values():
        t["stopped"] = False

# Render one frame (helper)
def render_frame(trains_dict):
    # Map center = average coords
    lats = [t["lat"] for t in trains_dict.values()]
    lons = [t["lon"] for t in trains_dict.values()]
    center = [sum(lats)/len(lats), sum(lons)/len(lons)]
    m = folium.Map(location=center, zoom_start=8, tiles="OpenStreetMap")
    # draw 4 simple tracks as polylines (offsets for visual top-down)
    base_line_start = (min(lats)-0.5, min(lons)-0.6)
    base_line_end = (max(lats)+0.5, max(lons)+0.6)
    colors = {1:"blue",2:"red",3:"green",4:"orange"}
    for track_no in [1,2,3,4]:
        offset_lat = 0.02*(track_no-2.5)
        folium.PolyLine([
            (base_line_start[0]+offset_lat, base_line_start[1]),
            (base_line_end[0]+offset_lat, base_line_end[1])
        ], color=colors[track_no], weight=4, opacity=0.3, tooltip=f"Track {track_no}").add_to(m)

    # add trains as markers
    for name, t in trains_dict.items():
        icon_color = "gray" if t.get("stopped", False) else ("red" if t["speed"]==0 else "green")
        folium.Marker(
            location=[t["lat"], t["lon"]],
            popup=f"{t['name']} — {t['route']}<br>Speed: {t['speed']} km/h<br>Track: {t['track']}",
            icon=folium.Icon(color=icon_color, icon="train", prefix="fa")
        ).add_to(m)

    map_placeholder.write("")   # ensure placeholder is ready
    st_folium(m, width=900, height=500, key="map")

    # left info
    with left_placeholder.container():
        st.subheader("Live Train Details")
        for name, t in trains_dict.items():
            status = "🟥 STOPPED" if t.get("stopped", False) or t["speed"]==0 else "🟩 MOVING"
            st.markdown(f"**{t['name']}** — {t['route']}")
            st.write(f"📍 Position: {t['lat']:.5f}, {t['lon']:.5f}")
            st.write(f"🛤 Track: {t['track']} | 🔁 Status: {status} | ⚡ Speed: {t['speed']} km/h")
            st.write(f"⏳ Distance to target: {t.get('distance',0):.2f} km")
            st.markdown("---")

# If not running, render initial map and stop.
render_frame(trains)

# Single alert shown variable
if "alert_shown" not in st.session_state:
    st.session_state.alert_shown = False

# Main simulation loop — controlled, not infinite
if st.session_state.running:
    frame = 0
    while frame < MAX_FRAMES and st.session_state.running:
        # 1) compute pairwise distances and decision logic
        names = list(trains.keys())
        # reset stopped flags to false before computing (they will be set below if needed)
        for t in trains.values():
            t["stopped"] = False

        # check conflicts pairwise
        for i in range(len(names)):
            for j in range(i+1, len(names)):
                a = trains[names[i]]
                b = trains[names[j]]
                d = distance_km(a["lat"], a["lon"], b["lat"], b["lon"])
                # update stored distances to their targets
                a["distance"] = distance_km(a["lat"], a["lon"], a["target"]["lat"], a["target"]["lon"])
                b["distance"] = distance_km(b["lat"], b["lon"], b["target"]["lat"], b["target"]["lon"])
                # if same track AND close -> one stops
                if a["track"] == b["track"] and d <= STOP_THRESHOLD_KM:
                    # decide which yields
                    yield_name = decide_yield(a, b)
                    trains[yield_name]["stopped"] = True
                    # show alert once
                    if not st.session_state.alert_shown:
                        alert_placeholder.warning(
                            f"🚨 Conflict: {a['name']} and {b['name']} on same track within {d:.2f} km. "
                            f"{yield_name} instructed to STOP to avoid collision."
                        )
                        st.session_state.alert_shown = True

        # 2) move each train towards target if not stopped
        # simulate time per frame: STEP_HOURS = (FRAME_SECONDS * speed_input) / 3600
        # step_km per frame = speed_km_per_hr * STEP_HOURS
        step_seconds = FRAME_SECONDS / speed_input  # speed input increases visual speed; smaller seconds -> faster frames
        for t in trains.values():
            t["distance"] = distance_km(t["lat"], t["lon"], t["target"]["lat"], t["target"]["lon"])
            if t.get("stopped", False):
                # maintain position but maybe set speed to 0 for UI clarity (but original speed preserved in data)
                pass
            else:
                # compute step_km for this frame (simulate speed varying)
                step_hours = FRAME_SECONDS / 3600.0 * speed_input
                step_km = t["speed"] * step_hours
                new_lat, new_lon = move_towards(t["lat"], t["lon"], t["target"]["lat"], t["target"]["lon"], step_km)
                t["lat"], t["lon"] = new_lat, new_lon

        # 3) re-render frame (replace, not append)
        render_frame(trains)

        # 4) sleep and continue — check stop button via session_state
        time.sleep(FRAME_SECONDS)
        frame += 1

    # after loop stops, turn off running so it doesn't re-run
    st.session_state.running = False
    # final message
    alert_placeholder.info("Simulation finished (or stopped). Press ▶ Start to run again or ↺ Reset to restore initial positions.")
