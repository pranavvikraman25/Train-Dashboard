import streamlit as st
from PIL import Image, ImageDraw
import time
import math

# --- Page Setup ---
st.set_page_config(page_title="Train Simulator", layout="wide")
st.markdown("## 🚆 Smart Train Safety Simulation – Chennai Division")

# --- Load assets ---
train_icon = Image.open("assets/train.png").resize((80, 80))
track_bg = Image.new("RGB", (800, 300), (200, 200, 200))
draw = ImageDraw.Draw(track_bg)
# draw rails
for i in range(0, 300, 50):
    draw.line([(0, i + 25), (800, i + 25)], fill="gray", width=3)

# --- Sidebar Metrics ---
with st.sidebar:
    st.header("📊 Live Train Data")
    speed = st.slider("Speed (km/h)", 0, 120, 80)
    distance = st.number_input("Distance to Next Train (km)", 30.0, 100.0, 40.0, 0.1)
    signal = st.selectbox("Signal Status", ["GREEN", "YELLOW", "RED"])
    st.write("---")
    st.metric("Current Speed", f"{speed} km/h")
    st.metric("Next Train Distance", f"{distance} km")
    st.metric("Signal", signal)

# --- Animation Settings ---
start_btn = st.button("▶ Start Simulation")
stop_btn = st.button("■ Stop")

if "running" not in st.session_state:
    st.session_state.running = False
if start_btn:
    st.session_state.running = True
if stop_btn:
    st.session_state.running = False

# --- Canvas Area ---
canvas = st.empty()
info_area = st.empty()

# --- Simulation Loop ---
pos_x = 0
direction = 1  # rightward
fps = 30
train_y = 150  # fixed on middle track

while st.session_state.running:
    frame = track_bg.copy()
    frame.paste(train_icon, (int(pos_x), train_y - 40), train_icon)

    # update position
    pos_x += direction * (speed / 10)
    if pos_x >= 720:
        direction = -1
        st.warning("🚦 Reached Station — changing direction!")
    elif pos_x <= 0:
        direction = 1

    # Draw additional info on frame
    d = ImageDraw.Draw(frame)
    d.text((10, 10), "Track: 2 | Route: Chennai–Bangalore", fill="black")
    d.text((10, 40), f"Speed: {speed} km/h", fill="black")
    d.text((10, 70), f"Signal: {signal}", fill="black")

    # Alert logic
    if signal == "RED" or distance < 10:
        st.error("🚨 ALERT: Stop immediately – train ahead or red signal!")
        speed = 0

    canvas.image(frame)
    time.sleep(1 / fps)

# --- Stopped Display ---
if not st.session_state.running:
    frame = track_bg.copy()
    frame.paste(train_icon, (int(pos_x), train_y - 40), train_icon)
    canvas.image(frame)
    info_area.info("🟢 Ready for next simulation run.")
