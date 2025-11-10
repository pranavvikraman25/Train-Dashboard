from geopy.distance import geodesic

def calculate_distance(train1, train2):
    pos1 = (train1["lat"], train1["lon"])
    pos2 = (train2["lat"], train2["lon"])
    return geodesic(pos1, pos2).km

def calculate_eta(distance, speed):
    if speed > 0:
        return round(distance / speed * 60, 2)  # in minutes
    return None

def get_status(train):
    if train["signal"] == 0 or (train["lat"] == 0 and train["lon"] == 0):
        return "🟥 STOP - Waiting for Clearance"
    elif train["speed"] <= 5:
        return "🟧 Slow / Signal Zone"
    else:
        return "🟩 Running Smoothly"
