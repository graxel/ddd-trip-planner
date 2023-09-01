import math
import random
import streamlit
import google_apis
import pandas as pd
import pydeck as pdk
import streamlit as st


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

    return lat_window, lon_window

def calculate_zoom_level(lat1, lon1, lat2, lon2, width_pixels):
    R = 6371  # Earth's radius in kilometers
    B = width_pixels  # Width of the map window in pixels

    delta_lon = abs(lon1 - lon2)
    lat_rad = math.radians(lat1)
    zoom = math.log2(360 * ((2 * R * math.cos(lat_rad) * math.pi) / (256 * B * delta_lon)))

    return int(zoom)

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

def range_test(ddd_row, rdm_rt_pt, search_distance):
    ddd_lat = ddd_row['latitude']
    ddd_lon = ddd_row['longitude']
    ddd_dist = haversine_distance(rdm_rt_pt, (ddd_lat, ddd_lon))
    return ddd_dist < search_distance

def package_route_points(route_points):
    route_points_df = pd.DataFrame(route_points, columns=['latitude', 'longitude'])
    route_df = route_points_df[['longitude', 'latitude']].apply(list, axis=1).to_frame()
    route_df['num'] = 0
    route_df = route_df.groupby('num').agg(**{
        'path': pd.NamedAgg(column=0, aggfunc=list)
    })
    return route_df

def find_ddds_along_route(ddds, route_points, filter_window, search_distance):
    lat_window, lon_window = filter_window
    remaining_ddds = ddds[
        (ddd_locations['latitude'] > lat_window[0]) &
        (ddd_locations['latitude'] < lat_window[1]) &
        (ddd_locations['longitude'] > lon_window[0]) &
        (ddd_locations['longitude'] < lon_window[1])
    ].copy()

    rdm_rt_pts = random.sample(route_points, len(route_points))
    ddds_in_range = pd.DataFrame()

    for rdm_rt_pt in rdm_rt_pts:
        if remaining_ddds.shape[0] == 0:
            break
        range_filter = remaining_ddds.apply(range_test, rdm_rt_pt=rdm_rt_pt, search_distance=search_distance, axis=1)
        new_ddds_in_range = remaining_ddds[range_filter]

        if new_ddds_in_range.shape[0] > 0:
            remaining_ddds = remaining_ddds.drop(new_ddds_in_range.index)
            ddds_in_range = pd.concat([ddds_in_range, new_ddds_in_range])

    return ddds_in_range

# Streamlit App Configuration
st.set_page_config(layout="wide", page_title="DDD Finder")

# Sidebar Input
st.sidebar.header("Plan your trip")
start_address = st.sidebar.text_input("From:")
end_address = st.sidebar.text_input("To:")
search_distance = st.sidebar.slider("Search Distance (miles):", min_value=0, max_value=50, value=20)

ddd_locations = pd.read_csv('ddd_locations.csv', na_values=['ERROR', 'ERROR, ERROR, ERROR ERROR'])
ddds_in_range = ddd_locations

icon_layer = pdk.Layer(type="IconLayer")
route_layer = pdk.Layer(type="PathLayer")

if start_address and end_address:
    route_points = google_apis.get_route_points(start_address, end_address)
    route_df = package_route_points(route_points)


    filter_window = calc_filter_window(route_points, search_distance)
    (lat1, lat2), (lon1, lon2) = filter_window
    map_center = [ (lat1 + lat2) / 2, (lon1 + lon2) / 2 ]
    map_zoom = calculate_zoom_level(lat1, lon1, lat2, lon2, width_pixels=800)
    

    ddds_in_range = find_ddds_along_route(ddd_locations, route_points, filter_window, search_distance)
    ddds_in_range['status'] = 'in_range'

    icon_size = 15
    icon_data = {
        'in_range': {
            # 'url': 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAB4AAAAeCAYAAAA7MK6iAAAACXBIWXMAAAsTAAALEwEAmpwYAAABe0lEQVR4nO2UOy9EQRiGH2wULg2iU1AoRGgkfoJtaBSiEImIqBR+gCAKpUShQyFqpcQlgtBYnSi3ECuCxm0L4ZWTzEkmm3MZ6+yp9k2+ZOY78+Y538x8A1VVFSBBneBUcCbIkJYEEwKZmE2z2lsL/ChoTgM8bkH9WEij2psA8KugvZLgmQCoH+uVgjYJChHgL0F/JcArEVA/vPaqSRLaJfh0AHsxlSR4PwJ0J3i35s+CtiSgYzEVen3cW3LbN/8LbRU8hAB/BEUzHhQ0CLas79uCxnLBuxGVXgt2zHjV8kwKPkz+tBzoaMwWLwmGzPjee1ws75zJ5/8K7TCXJAo8YF4yv7eHLf+BdRxZV2hGcB4Dzfv9Klg0uUsz7zFAf23B6ZZ75+XQq8vW+hbBm8l7W78RsH4vDpoVfDuAu0t8ayafK+lpO6bDoJ2CJwfoYYDXq/olxlcU9AWBrxyfxJGQH5938OaCjEcOxhNBbQi4XnAR4z+OPOuqqiIB/QIfJQd9B/OxFwAAAABJRU5ErkJggg==',
            'url': 'data:image/png;base64,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',
            'width': icon_size,
            'height': icon_size,
            'anchorY': icon_size,
        },
        'out_of_range': {
            'url': 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAEMAAABDCAYAAADHyrhzAAAACXBIWXMAAAsTAAALEwEAmpwYAAAHIklEQVR4nOWbS2hjVRjHT8dRZhwUFBXXKoqL7hREUATRlY5Lca2guJBZCCIiiAs3IsxsXAgz4sKFL+zMpG0eTdI006ZN0+Q2t3k079dtHpfc3iS1bdo0n3xhroR67iOZe2+azB++XZJz7u+e873OCSEjFgBcBIDHAOARcr8IAB7mef6TaDRqDQQCSa/XKy4sLBzZbLaOxWLpWq3WE7vdfuzxePbW1tYKLMuulEql7wDgaTIJAoCpSqXyMcMwmw6H42hmZgYGtbm5ua7f78/n8/lruIrIOELgOO4bn89Xu3nz5sAA5Mztdu+nUqnfAeASGQfxPP9mIBDI6wnhtC0uLv5TKpW+Jmd5NWQymRvz8/MnRkHot1u3bgHLskEAeJScJQHAhXA4zGpdDfg5h8MBKysrEAgEgGEYCAaDsLa2Bi6Xq/egWqHcuXNnVxTFl8hZkCiKj6OD0/Im19fXgeM4aLfboKSTkxPgeR7C4TDMz8+rAnG5XAe1Wu2dkYIAgIt+v7+kNFGLxQLRaFQVgBKYfD7fW0lK4zidzjbP82+MCsS5UCgUV5ogLvuDg4OhINCgxGIxxS2EOYoois+aDiOZTP6htCUymQwYoXq9DjabTRYIRjIAeMA0EJVK5YPZ2dkubTK3b9+GarUKRmp/fx+3hSyQZDL5pykgAOD8ysoKL7cijAYh6fDwUNaPWK3WTr1ef9VwGJlM5rrcG0FHZ6ZarVbPQdPmEgwGtw0FAQAPopOS2auqk5+dnf3flsLQiW/Y7XZjztDLOQqFAhwfH2sCgp+Vi2I8z182DEYul7tKG3hubq63bAeFoSUkYxRR0/LyMvU3QqEQaxgMv0xOkUwmNb1FCQY+INrR0VHPGe7t7fWiRC6Xg83NTdzz/QmVangWRZEKA9sDAPCk7iBardY09h1OD4gPqHVJ98NQUrfb7YVmyR8sLCz0wCnJ5/NRgWSz2Z90h5HJZG7QBsM9rlVaYfS/cek7aj6pXC5TYWxsbMR1hxEKhSK0wbCGMArG6YdEOHLC36RFFqxbdE/CvF5vg5ZgDfJgw8BAYXWrZRXStgrmPu12e1rXEt1ms3VOD7S0tDTQQw0LAyvduw5R8XPxeJy6VXZ2dr7SDUa73Z6m9SqwB2EGDKx4pTGVQnipVJJLz3/VDYYgCO/RBolEIqbAQGEuo+Y30H/R5hmPxy26wahWq5/SBtne3jYNht1u730X85FB841IJOLWDUalUrlCGwT7C2bBkDpeSitDEAQqjK2tLY9uMOr1+vu0QViWNQUGJlzSmErJF1bMtHniwZVuMADgOVqHaXV11RQYOzs7ve9hQackzFppMNLp9M+Gh1aHyuT0giEVYmoOG+samdCq7xnL4uLiPm0gLLSMhFEsFv9LntTGkut+iaL4tq4wfD5flTZQNps1DAam4pjl3g2Pip/Fypc2P2xP6l65sizrow02SBaqFQZ2sEKhUO+wCT+PaTZWssNkn3jaT/RWoVCgNnbQMKQNAgPzk0Qi0QvN6Adwr+PDo2/o72WgbWxsqMLrdDqyh00MwzC6w2g2my9KS/a0YSE1CAw1w3FwNdRqNU2/m0qlZH8LWw/ECHkplWufx1adNDaM0cfQDLtc+BuYVA3iYLELJtcURqiNRuMVQ2BEo1GnHAxcpnqdnmkV+hGpvJdZsTwxSoIgXFY63vN6vUOl2sMKG8ZK2y2RSPxt6B0Mr9crqp2vmgEknU6r+Z2uKIovEyOVTCb/UnOAuHS1NomHkVwY7Te8JkGMVrPZfMJmsx2rTQZTdaUKcxhhkwfrIS0RSdfulpJYll3VMiFMmrCyHfZuRr+jxGgjNXjUDKOeaSfxgiC8JncKTzMMfVtbW9BsNgdeCViJql1UOW3pdPoXYqbC4XBwkAn2n5Dh9SQ8I93d3e3VFNLJGsLCXAN9Ap67DnK3SzI8Czb9vmir1ZrGo/9hgBhpeHmWjELRaHRp1A/fb8vLy3VTb+30q9VqPYUnVqOGIKXeHMd9RkapQqHwg5G3gbUawzBhMmoBwNT6+nphlCDw3wiNRuMFchYkCMLrtB6pGYarMpfL/UjOkrLZ7E+j2C7BYBBvykyRsyQAmAoEAhkzQTidzsORXILV2g3DCZoVPYrF4pfkLIvjuI8GSdWHtVgs5iTjoEQiMWMkCL/fz+E1TDIOAoBzDMMoXrK/l38hNRqN58k4CQAura6uUg+ehjW73d4pl8vvknGUKIrPeDyelh4g0A+VSqXPyTirUqm8hRnivYC4+5eN62QSxHHclXuJMPF43EEmSfl8/tthgEQiET86ZDJpyuVyV7GFrxVEGFtiAOfJpCqbzV6TOw7st83NzchEg5CEzlDuEBsNcxQAeIjcL8rn89/TfEg4HGbGJrvUU8Vi8QupqYzlfywW80yks9Sqcrn8ocvlOkylUr9p/tIkCwAujHoOqH8BDGYMYNhnwCsAAAAASUVORK5CYII=',
            'width': icon_size,
            'height': icon_size,
            'anchorY': icon_size,
        },
        'test': {
            'url': 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAEMAAABDCAYAAADHyrhzAAAACXBIWXMAAAsTAAALEwEAmpwYAAAFeUlEQVR4nO2beahWRRjGf2WZthjXFmixQMK0iMwWbSMlSlqstIiQlJSM9j/EkIwys5VWKSsLBFGQILLCpSLbpLAgsiTI5FZoC7frLdosS3tiOPPR5+XMOTPnO3O+71594P3nMjPPe55vlnfedy7sRnMgOEIwSfCIYIVgveArwU+CzYIvBG8LnhXcIjhBsAe9BYJBglmCzwUqYB2CJwWn0VMhOF6wRPBPQRHS7APBRfQUCA4UzBNsL1GE7vauEZtWhmCM4LuIItTbNsH0ltxTBLcHzIYdgnbBKsFiwQLBQsEywWf2Q31FeVmwH60AwZ6Cpzyc/lPwguAKwcE5Y/azs+wJu4Hmjb02b8xKoOQYzHL0V8G9RZ0V9BVMtTMpi2ed2a/K/0JPCO7OcfAlE1uUxNXP8v2dwfeOEa8MviAILhb8m7G53RCJ93QboLkEmReD1wnBYYItDmd+F5xP/EDOFcSZH2hcTP6dIFiaMSPGUgEEhwi+dPixSbB/FU6MzpiiU6I7sLMvQwW/OXy5rwoH3nKQL/Ho+3PKkvrRnhTr7NjmdLpaMMDTn8kZp9jAUj46Deay5CDuMtO2gBhZ9otgrjlFPMZ90zHGXcSCkkgxjfQ2z/41MUzssI+gTXCkYLDgDME0e0P9tm7sTwWH54x7ouNk+zpKuK7E+bRf1vztgFAxctr1MUezneqm/Ya8gEqw3PFDnR36rY1snM8EjOElRl374TbxY/oszml7qcO/BygbgjkOstGxxLB9xtXFDydltOtr95nu/n1I2RCsTCH6wyyfmGLYfq/5zELHUjHh+14hfLmwucruRO8HjlFUjMttv8057e50zN4hIXx4bGg7UkgWViTGQXWnxaEZ7a50iHFBCJ9PKq/hzamoGLZv7S40PKPNOQ4/rwrlc8LGAmkkd1QoRm2ZnpnRZoTDz2mhfE4IjnaQzKlQjA6PmTHK4ef1oXx5azaN5PGK9oy2uj2jLaPdWIefk0L4MmFCWsFfKSSvVCTGBNtvY067Gx1inBvCV/Roba9IjNpF7KGcdvMdYhwbwpcLwRoH0aDIEejEusRRJldG9qvcRI+SUmFDm1OBu4nJs271uY7bm2/azbWTsiG41SGGdxQacGsdIni+LtAzFfs+OX1mO/xbEfKdvh9yioPM2MhAMUxVfqbgHsGDgqcFzwneEHzfbexFeQkeQX/BD2XEQl4Q7G3TdGmEqzzH8M10bbWXrvM8x52eMdaYhj8+4OZas/Ee/a8RXOewawWX2SgyN9XXrWyRdnWX/fH2JQYEUzLE6MhLz0Wq89au92m2NCZ5W06F/L2QX7UEf+bmLLcJsR1YnuPAsirqnfbNV5YfJn/aP7YTl3hsgK/7JokLXg1cx2i9zY/Bn7ZON3o4Y0p/IygR5lmD4FUPbhN8DS2Tu5EpWjPzuO2xRitbJodpayqdnrwrG+ELglkCGVV41/p9WDCswEy42eOhStxbah4EMwIdrNl6+zzJ1FNPtXeKNvvMwDyXHG/uIfZxbMjbrpqtpmooeUmzqaAgsczsFaMqF8PARo1qIXuRZkHJybK2BUSo3WcGN00MA8HJkV8D+9osWgFyp9uqsg0hZc6oEAwQfNMkIbZn1VKaAsFZTVou99OKEDxasRCfNOURbEDs8XFFQpjEzXG0MpSUIrsqEGMyPQFK0neup9Rl2AJ6EuSXcyhia1rmGA1MwiwqWYh2n/emLQkl5YXVJQmxpdTnSM2AYKD9f9VGhNgWrf5RNQTHBGSpupvZiCfSm6DkgWtXASFuojdCMDKj+pVmM+nNUPJg3vU/InELxq0IJf+m6SpiG5vNrgQlyeDOlD1iBrsiBMPqksqmxjKVXRmCowQfCS5sti+7wf/4D6AHt6ZJ1eZ7AAAAAElFTkSuQmCC',
            'width': icon_size,
            'height': icon_size,
            'anchorY': icon_size,
        },
    }

    ddds_in_range['icon_data'] = ddds_in_range['status'].map(icon_data)


    icon_layer = pdk.Layer(
        type="IconLayer",
        data=ddds_in_range,
        get_icon="icon_data",
        get_size=15,
        # size_scale=15,
        get_position=['longitude', 'latitude'],
        pickable=True,
        auto_highlight=True
    )

    route_layer = pdk.Layer(
        type="PathLayer",
        data=route_df,
        # pickable=True,
        get_color=(0, 128, 255),
        width_scale=20,
        width_min_pixels=2,
        get_path="path",
        get_width=5,
    )

# Display Map
st.header("Map")







st.pydeck_chart(pdk.Deck(
    map_style='mapbox://styles/mapbox/streets-v12', #https://docs.mapbox.com/api/maps/styles/
    tooltip={
        'html': '''<small>
        {loc_name}<br>
        {full_address}
        </small>''',
        'style': {
            'color': 'white'
        }
    },
    initial_view_state=pdk.ViewState(latitude=38, longitude=-97, zoom=3, pitch=20),
    layers=[route_layer, icon_layer]
))


# Display Table
st.header("ddds_in_range")
st.table(ddds_in_range)


