import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
import geopy.distance
import geopandas as gpd
from shapely.geometry import Point, shape
import folium
import os
import shutil
import json

# Constants
NUM_PHONES = random.randint(5, 10)
CALLS_PER_PHONE = (10, 100)
CALL_DURATION_RANGE = (30, 300)  # in seconds (30 seconds to 5 minutes)
START_DATE = datetime(2024, 6, 1)
END_DATE = datetime(2024, 7, 4)
AREA_CODES = {
    'Toronto': ['416', '647', '437'],
    'NYC': ['212', '646', '332', '917']
}
COUNTRY_CODE = '1'
MAX_TRAVEL_SPEED_KMH = 90  # Maximum travel speed in km/h
ANCHOR_PROXIMITY_KM = 5  # Proximity distance for the anchor point
ANCHOR_CALL_PERCENTAGE = 0.6  # 60% of calls within 5 km of anchor

TORONTO_CITY_HALL = (43.6529, -79.3849)
QUEENS_NEW_YORK = (40.7282, -73.7949)
DISTANCE_LIMITS = {
    'Toronto': 100,  # in km
    'NYC': 50       # in km
}

# Load the GeoJSON file with polygons
geojson_path = '../static/polygon.json'
with open(geojson_path) as f:
    geojson_data = json.load(f)

land_polygons = [shape(feature['geometry']) for feature in geojson_data['features']]

# Function to check if coordinates are over land based on GeoJSON polygons
def is_land(latitude, longitude):
    point = Point(longitude, latitude)
    return any(polygon.contains(point) for polygon in land_polygons)

# Function to generate random phone numbers
def generate_phone_number(area_codes):
    return f"+{COUNTRY_CODE}{random.choice(area_codes)}{random.randint(1000000, 9999999)}"

# Function to generate random geographical coordinates within a specified distance, favoring closer distances
def generate_random_coordinates(center, max_distance_km, favor_closer=True):
    while True:
        if favor_closer:
            # Exponential distribution to favor closer distances
            distance_km = np.random.exponential(scale=max_distance_km / 2)
        else:
            # Normal distribution for more spread distances
            scale = max(max_distance_km / 3, 0.1)  # Ensure the scale is positive
            distance_km = min(np.random.normal(loc=max_distance_km / 2, scale=scale), max_distance_km)
        
        distance_km = max(0, min(distance_km, max_distance_km))  # Ensure distance is within bounds
        bearing = random.uniform(0, 360)
        destination = geopy.distance.distance(kilometers=distance_km).destination(center, bearing)
        if is_land(destination.latitude, destination.longitude):
            return destination.latitude, destination.longitude

# Function to generate realistic coordinates based on travel constraints
def generate_realistic_coordinates(previous_coords, previous_time, current_time):
    max_distance_km = max((current_time - previous_time).total_seconds() / 3600 * MAX_TRAVEL_SPEED_KMH, 0.1)
    return generate_random_coordinates(previous_coords, max_distance_km, favor_closer=False)

# Function to convert seconds to hours and minutes format
def format_time(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    return f"{hours}h {minutes}m"

# Function to generate call data
def generate_call_data(num_calls, phone_numbers, area_codes, own_phone, anchor_point):
    call_data = []
    call_times = sorted([START_DATE + timedelta(seconds=random.randint(0, int((END_DATE - START_DATE).total_seconds()))) for _ in range(num_calls)])
    previous_coords = None
    previous_time = None
    for i, call_time in enumerate(call_times):
        call_duration = random.randint(*CALL_DURATION_RANGE)
        if random.random() < ANCHOR_CALL_PERCENTAGE:
            # 60% of the calls are made within 5 km of the anchor point, favoring closer distances
            latitude, longitude = generate_random_coordinates(anchor_point, ANCHOR_PROXIMITY_KM, favor_closer=True)
        else:
            # 40% of the calls are made within the normal distance limits
            if area_codes in AREA_CODES['Toronto']:
                latitude, longitude = generate_random_coordinates(TORONTO_CITY_HALL, DISTANCE_LIMITS['Toronto'])
            else:
                latitude, longitude = generate_random_coordinates(QUEENS_NEW_YORK, DISTANCE_LIMITS['NYC'])
        
        other_phone = random.choice(phone_numbers)
        direction = "Incoming" if own_phone == other_phone else "Outgoing"
        distance = geopy.distance.distance(previous_coords, (latitude, longitude)).km if previous_coords else 0
        distance_from_anchor = geopy.distance.distance(anchor_point, (latitude, longitude)).km
        time_diff = (call_time - previous_time).total_seconds() if previous_time else 0
        google_maps_link = f"https://www.google.com/maps/search/?api=1&query={latitude},{longitude}"
        call_data.append([call_time, other_phone, call_duration, latitude, longitude, direction, distance, google_maps_link, time_diff, distance_from_anchor])
        previous_coords = (latitude, longitude)
        previous_time = call_time
    return call_data

# Generate unique phone numbers
phones = [generate_phone_number(AREA_CODES[random.choice(list(AREA_CODES.keys()))]) for _ in range(NUM_PHONES)]

# Generate anchor points for each phone
anchors = {}
for phone in phones:
    area_code = phone[2:5]
    if area_code in AREA_CODES['Toronto']:
        anchors[phone] = generate_random_coordinates(TORONTO_CITY_HALL, DISTANCE_LIMITS['Toronto'])
    else:
        anchors[phone] = generate_random_coordinates(QUEENS_NEW_YORK, DISTANCE_LIMITS['NYC'])

# Dictionary to store DataFrame for each phone
phone_data = {}

# Ensure the directory for saving maps exists and is empty
map_dir = "../results/checkmap"
if os.path.exists(map_dir):
    shutil.rmtree(map_dir)
os.makedirs(map_dir, exist_ok=True)

# Generate call data for each phone and store in the dictionary
for phone in phones:
    num_calls = random.randint(*CALLS_PER_PHONE)
    area_code = phone[2:5]
    call_data = generate_call_data(num_calls, phones, area_code, phone, anchors[phone])
    df = pd.DataFrame(call_data, columns=['Call Time', 'Number', 'Call Duration (s)', 'Latitude', 'Longitude', 'Direction', 'Distance (km)', 'Google Maps Link', 'Time Since Last Call (s)', 'Distance from Anchor (km)'])
    phone_data[phone] = df

    # Create a folium map for the phone
    m = folium.Map(location=[anchors[phone][0], anchors[phone][1]], zoom_start=10)
    
    # Add marker for the anchor point
    folium.Marker(
        location=[anchors[phone][0], anchors[phone][1]],
        popup=f"Anchor Point<br>Latitude: {anchors[phone][0]}<br>Longitude: {anchors[phone][1]}",
        icon=folium.Icon(color='red', icon='info-sign')
    ).add_to(m)
    
    # Add markers for each call
    for _, row in df.iterrows():
        folium.Marker(
            location=[row['Latitude'], row['Longitude']],
            popup=f"Time: {row['Call Time']}<br>Number: {row['Number']}<br>Duration: {row['Call Duration (s)']}<br>Direction: {row['Direction']}<br>Distance: {row['Distance (km)']} km<br>Distance from Anchor: {row['Distance from Anchor (km)']} km<br><a href='{row['Google Maps Link']}' target='_blank'>Google Maps</a>",
            icon=folium.Icon(color='blue' if row['Direction'] == 'Outgoing' else 'green')
        ).add_to(m)
    
    # Save the map to an HTML file
    map_path = os.path.join(map_dir, f"map_{phone}.html")
    m.save(map_path)

# Ensure each phone has at least one call to/from another phone with a worksheet
for i, phone in enumerate(phones):
    other_phone = random.choice(phones[:i] + phones[i+1:])
    call_time = START_DATE + timedelta(seconds=random.randint(0, int((END_DATE - START_DATE).total_seconds())))
    call_duration = random.randint(*CALL_DURATION_RANGE)
    area_code = other_phone[2:5]
    if area_code in AREA_CODES['Toronto']:
        latitude, longitude = generate_realistic_coordinates((phone_data[other_phone].iloc[-1]['Latitude'], phone_data[other_phone].iloc[-1]['Longitude']), phone_data[other_phone].iloc[-1]['Call Time'], call_time)
    else:
        latitude, longitude = generate_realistic_coordinates((phone_data[other_phone].iloc[-1]['Latitude'], phone_data[other_phone].iloc[-1]['Longitude']), phone_data[other_phone].iloc[-1]['Call Time'], call_time)
    distance = geopy.distance.distance((phone_data[other_phone].iloc[-1]['Latitude'], phone_data[other_phone].iloc[-1]['Longitude']), (latitude, longitude)).km
    distance_from_anchor = geopy.distance.distance(anchors[other_phone], (latitude, longitude)).km
    google_maps_link = f"https://www.google.com/maps/search/?api=1&query={latitude},{longitude}"
    time_diff = (call_time - phone_data[other_phone].iloc[-1]['Call Time']).total_seconds()
    new_call = pd.DataFrame([{
        'Call Time': call_time,
        'Number': phone,
        'Call Duration (s)': call_duration,
        'Latitude': latitude,
        'Longitude': longitude,
        'Direction': 'Incoming',
        'Distance (km)': distance,
        'Google Maps Link': google_maps_link,
        'Time Since Last Call (s)': time_diff,
        'Distance from Anchor (km)': distance_from_anchor
    }])
    phone_data[other_phone] = pd.concat([phone_data[other_phone], new_call], ignore_index=True)

# Convert the 'Time Since Last Call (s)' column to hours and minutes format
for phone, df in phone_data.items():
    df['Time Since Last Call (s)'] = df['Time Since Last Call (s)'].apply(format_time)

# Create an Excel writer
excel_path = 'phone_calls.xlsx'
writer = pd.ExcelWriter(excel_path, engine='xlsxwriter')

# Write each DataFrame to the respective sheet
for phone, df in phone_data.items():
    df.to_excel(writer, sheet_name=phone, index=False)

# Save and close the writer
writer.close()

print(f"Sample phone call data has been generated and saved to {excel_path}")
print(f"Maps have been saved to the '{map_dir}' directory")
