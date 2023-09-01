import math

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

# Example coordinates for two points
lat1 = 52.5200  # Latitude of point 1 (Berlin, Germany)
lon1 = 13.4050  # Longitude of point 1
lat2 = 48.8566  # Latitude of point 2 (Paris, France)
lon2 = 2.3522   # Longitude of point 2

if __name__ == "__main__":
	print(haversine_distance((lat1, lon1), (lat2, lon2)))
