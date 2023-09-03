import os
import json
import urllib3
import requests
import haversine

api_key = os.environ['GOOGLE_MAPS_API_KEY']

def get_route_points(start_address, end_address):
    base_url = 'https://maps.googleapis.com/maps/api/directions/json'
    params = {
        'origin': start_address,
        'destination': end_address,
        'key': api_key
    }
    
    print('requesting route...')
    response = requests.get(base_url, params=params)
    data = response.json()
    print('got response.')

    if data['status'] == 'OK':
        overview_polyline = data['routes'][0]['overview_polyline']['points']
        route_points = decode_polyline(overview_polyline)
        return route_points
    else:
        print("Directions request failed. Status:", data['status'], flush=True)
        return []

def get_lat_lon(address):
    base_url = 'https://maps.googleapis.com/maps/api/geocode/json'
    params = {
        'address': address,
        'key': api_key
    }
    response = requests.get(base_url, params=params)
    data = response.json()
    if data['status'] == 'OK':
        point = data['results'][0]['geometry']['location']
        latitude = point['lat']
        longitude = point['lng']
        return (latitude, longitude)
    else:
        print("Geocoding failed. Status:", data['status'])
        return (None, None)

def decode_polyline(polyline_str):
    index, lat, lng = 0, 0, 0
    coordinates = []
    changes = {'latitude': 0, 'longitude': 0}

    # Coordinates have variable length when encoded, so just keep
    # track of whether we've hit the end of the string. In each
    # while loop iteration, a single coordinate is decoded.
    while index < len(polyline_str):
        # Gather lat/lon changes, store them in a dictionary to apply them later
        for unit in ['latitude', 'longitude']: 
            shift, result = 0, 0

            while True:
                byte = ord(polyline_str[index]) - 63
                index+=1
                result |= (byte & 0x1f) << shift
                shift += 5
                if not byte >= 0x20:
                    break

            if (result & 1):
                changes[unit] = ~(result >> 1)
            else:
                changes[unit] = (result >> 1)

        lat += changes['latitude']
        lng += changes['longitude']

        coordinates.append((lat / 100000.0, lng / 100000.0))

    return coordinates

if __name__ == "__main__":
    start_address = 'yamunanagar, India'
    end_address = 'Delhi, india'
    points = get_route_points(start_address, end_address)
    print(max([haversine.haversine_distance(pt1, pt2) for pt1, pt2 in zip(points, points[1:])]))
