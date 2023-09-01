import os
import math
import random
import folium
import requests
import google_apis
import numpy as np
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium, folium_static

def load_ddds():
    all_ddd_locations = pd.read_csv('ddd_locations.csv', 
        na_values=['ERROR', 'ERROR, ERROR, ERROR ERROR'])\
        .dropna()\
        .sample(frac=1)\
        .reset_index(drop=True)
    all_ddd_locations['route_order'] = float('nan')
    all_ddd_locations['range'] = float('nan')
    all_ddd_locations['range_status'] = float('nan')
    return all_ddd_locations

def calc_filter_window(route_points, search_distance):
    # search_distance in kms
    lats = [point[0] for point in route_points]
    lons = [point[1] for point in route_points]
    rt_min_lat = min(lats)
    rt_max_lat = max(lats)
    rt_min_lon = min(lons)
    rt_max_lon = max(lons)

    lon_offset= (search_distance * 360) / (2 * math.pi * 6371.0 * math.cos(math.radians(rt_max_lat)))
    lat_offset = search_distance/111.0

    lat_window = rt_min_lat - lat_offset, rt_max_lat + lat_offset
    lon_window = rt_min_lon - lon_offset, rt_max_lon + lon_offset

    ne_point = rt_max_lat + lat_offset, rt_max_lon + lon_offset
    sw_point = rt_min_lat - lat_offset, rt_min_lon - lon_offset

    return sw_point, ne_point

def haversine_distance(pt1, pt2):
    r = 6371.0  # Earth's radius in kilometers

    lat1, lon1 = pt1
    lat2, lon2 = pt2

    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    delta_lat = lat2_rad - lat1_rad
    delta_lon = lon2_rad - lon1_rad

    a = math.sin(delta_lat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance = r * c  # Distance in kilometers
    return distance

def range_calc(ddd_row, rdm_rt_pt):
    ddd_lat = ddd_row['latitude']
    ddd_lon = ddd_row['longitude']
    return haversine_distance(rdm_rt_pt, (ddd_lat, ddd_lon))

def find_ddds_along_route(ddds, route_points, filter_window, search_distance):
    sw_point, ne_point = filter_window
    coord_filter = (ddds['latitude'] > sw_point[0]) & (ddds['latitude'] < ne_point[0]) &\
                   (ddds['longitude'] > sw_point[1]) & (ddds['longitude'] < ne_point[1])

    ddds['range_status'] = np.where(coord_filter, 'calculating', 'out_of_range')
    rdm_rt_pts = random.sample(list(enumerate(route_points)), len(route_points))
    for idx, rdm_rt_pt in rdm_rt_pts:
        calcing = ddds['range_status'] == 'calculating'
        if ddds[calcing].shape[0] == 0:
            break
    
        ddddist = ddds.loc[calcing, ['latitude', 'longitude']].apply(range_calc, rdm_rt_pt=rdm_rt_pt, axis=1)
        ddds.loc[calcing, 'range_status'] = np.where(ddddist < search_distance, 'in_range', 'calculating')
        ddds.loc[ddds['range_status'] == 'in_range', 'route_order'] = idx
    ddds.loc[ddds['range_status'] == 'calculating', 'range_status'] = 'out_of_range'
    ddds_in_range = ddds[ddds['range_status'] == 'in_range']
    return ddds_in_range


def render_map(route_points, ddd_locations):
    m = folium.Map(location=[48,-114], zoom_start=3, zoom_control=False)

    if len(route_points)>0:
        pl = folium.PolyLine(
            [[lat,lon] for lat,lon in route_points],
            color='blue',
            weight=3,
            opacity=0.5
        )
        pl.add_to(m)

    for _, ddd_loc in ddd_locations.iterrows():
        popup = folium.Popup(f"<b>{ddd_loc['loc_name']}</b><br>{ddd_loc['full_address']}", max_width=150)
        marker = folium.CircleMarker(
            [ddd_loc['latitude'], ddd_loc['longitude']],
            radius=5,
            color='red',
            fill=True,
            popup=popup
        )
        marker.add_to(m)

    folium_static(m, width=700, height=500)

def fetch(session, start_address, end_address):
    try:
        api_key = os.environ['GOOGLE_MAPS_API_KEY']
        base_url = 'https://maps.googleapis.com/maps/api/directions/json'
        params = {
            'origin': start_address,
            'destination': end_address,
            'key': api_key
        }
        print('making request')
        api_response = session.get('https://maps.googleapis.com/maps/api/directions/json?origin=miami&destination=orlando&key=AIzaSyCiyjY_UNrEP9nXw_ZFqd2UCtz6tr2-BjI')
        # api_response = session.get(url, params=params)
        print('got response')
        return result.json()
    except Exception:
        print('error')
        print(Exception)
        return {'status': 'Not OK'}

session = requests.Session()
st.set_page_config(layout="wide", page_title="DDD Finder")

st.sidebar.header("Plan your trip")
with st.sidebar.form("my_form"):
    start_address = st.text_input("From:")
    end_address = st.text_input("To:")
    search_distance = st.slider("Search Distance (miles):", min_value=0, max_value=120, value=20)
    submitted = st.form_submit_button("Submit")

all_ddd_locations = load_ddds()
ddds_in_range = all_ddd_locations
route_points = []

if submitted:
    data = fetch(session, start_address, end_address)
    st.write(data)
    if data['status'] == 'OK':
        overview_polyline = data['routes'][0]['overview_polyline']['points']
        route_points = google_apis.decode_polyline(overview_polyline)
        # return route_points
    else:
        print("Directions request failed. Status:", data['status'], flush=True)
        # return []

    # route_points = google_apis.get_route_points(start_address, end_address)
    if len(route_points) > 0:
        filter_window = calc_filter_window(route_points, search_distance)
        ddds_in_range = find_ddds_along_route(all_ddd_locations, route_points, filter_window, search_distance)

# start_address = 'luray, va'
# end_address = 'boston'
# search_distance = 10

# print(start_address, end_address, search_distance)



# if (
#     (start_address != '') and
#     (end_address != '') and
#     (search_distance is not None)
# ):
#     route_points = google_apis.get_route_points(start_address, end_address)
#     if len(route_points) > 0:
#         filter_window = calc_filter_window(route_points, search_distance)
#         ddds_in_range = find_ddds_along_route(all_ddd_locations, route_points, filter_window, search_distance)


# print(route_points)
# print('\n\n')
# print(ddds_in_range)


st.header('DDD Locations on Route')
render_map(route_points, ddds_in_range)


