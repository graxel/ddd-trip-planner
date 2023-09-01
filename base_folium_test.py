# import folium
# import streamlit as st
# from streamlit_folium import st_folium

# m = folium.Map([45,0], zoom_start=4)

# num = float(st.text_input("offset:", 0))
# points = [
#     ([45,0+num],'note1'),
#     ([45,1-num],'note2'),
#     ([45+num,2],'note3'),
#     ([45-num,3],'note4'),
# ]
# for coords, note in points:
#     pp = folium.Popup(note, parse_html=True)
#     cm = folium.CircleMarker(
#         location=coords,
#         color='red',
#         radius=5,
#         fill=True,
#         popup=pp,
#     )
#     cm.add_to(m)

# map_data = st_folium(m)#, width=1500, height=300)

# st.write(map_data)




import streamlit as st
import folium
from streamlit_folium import st_folium, folium_static

# Sample data with lat-lon points and additional information
data = [
    (37.7749, -122.4194, 'Point 1', 'Info for Point 1'),
    (34.0522, -118.2437, 'Point 2', 'Info for Point 2'),
    (40.7128, -74.0060, 'Point 3', 'Info for Point 3')
]

# Create a folium map
m1 = folium.Map(location=[38,-96], zoom_start=4, zoom_control=False)
m2 = folium.Map(location=[38,-96], zoom_start=4, zoom_control=False)

pl = folium.PolyLine([[lat,lon] for lat,lon,pt,info in data], color='blue', weight=3, opacity=0.75)
pl.add_to(m1)
pl.add_to(m2)

# Add points and popups to the map
for lat, lon, name, info in data:
    folium.Marker([lat, lon], popup=f"<b>{name}</b><br>{info}").add_to(m1)
    folium.CircleMarker([lat, lon], radius=5, color='red', fill=True, popup=f"<b>{name}</b><br>{info}").add_to(m2)


# old folium hack
# st.write(m._repr_html_(), unsafe_allow_html=True)

# st.write('markers + folium_static')
# folium_static(m1, width=700, height=500)
# st.write('')

st.write('circles + folium_static')
folium_static(m2, width=700, height=500)
st.write('')

# st.write('markers + st_folium')
# st_folium(m1, width=700, height=500)
# st.write('')

st.write('circles + st_folium')
st_folium(m2, width=700, height=500)
