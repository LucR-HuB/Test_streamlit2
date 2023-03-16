import streamlit as st
import folium
from streamlit_folium import folium_static, st_folium
from folium.raster_layers import WmsTileLayer
import json
import requests
import os
from shapely.geometry import Point, Polygon, shape
from folium.plugins import HeatMap
from folium.plugins import MarkerCluster

st.set_page_config(layout="wide")

'''
# 🌍 Welcome to PanoMapper! 🛸
'''
total_detections = 0
total_surface = 0.0
total_kWp = 0.0

def geocode(address):

        url = "https://nominatim.openstreetmap.org/search?"
        response = requests.get(url, params={
            'q': address,
            'format': 'json'
        })
        if response.status_code == 200:
            json_response = response.json()
            if len(json_response) > 0:
                return [json_response[0]['lat'], json_response[0]['lon']]
        return [0, 0]

def remove_marker(e):
    marker = e.target
    marker_cluster.remove_layer(marker)

# Charger les tuiles GeoJSON depuis Google Drive
with open("dalles_ign_33_WGS84.geojson", "r") as f:
    tiles_geojson = json.load(f)

# Charger les détections GeoJSON depuis Google Drive
with open("arrays_33.geojson", "r") as f:
    detections_geojson = json.load(f)

with open('array_33_centroides.geojson') as f:
    data = json.load(f)


# Création de la carte de base
latitude = 44.856177683344065
longitude = -0.5624631313653328

base_url = "https://wxs.ign.fr/essentiels/geoportail/wmts"
final_url = "https://wxs.ign.fr/essentiels/geoportail/wmts?layer=ORTHOIMAGERY.ORTHOPHOTOS&tilematrixset=PM&Service=WMTS&Request=GetTile&Version=1.0.0&Format=image/jpeg&TileCol={x}&TileRow={y}&TileMatrix={z}&STYLE=normal"

m = folium.Map(location=[latitude, longitude], zoom_start=13, tiles=final_url, attr='IGN-F/Géoportail', max_zoom = 19)

global_heatmap = st.button("GLOBAL HEATMAP")

'''
## Type your address below to start detection in your neibourhood! :robot_face:
'''

address = st.text_input('  ')
address_coordinates = ''

if address:
    address_coordinates = [float(coord) for coord in geocode(address)]
    m = folium.Map(location=[address_coordinates[0], address_coordinates[1]], zoom_start=28, tiles=final_url, attr='IGN-F/Géoportail', max_zoom = 19)
    folium.Marker(location=address_coordinates, tooltip=address).add_to(m)
    # Centering the map on the address
    m.fit_bounds([[address_coordinates[0], address_coordinates[1]], [address_coordinates[0], address_coordinates[1]]])

tile_name = ''

if address_coordinates:
    for tile in tiles_geojson["features"]:
        tile_geom = shape(tile["geometry"])
        if tile_geom.contains(Point(address_coordinates[1], address_coordinates[0])):
            tile_name = tile["properties"]["NOM"]

# Retrieving surrounding tiles
if tile_name:

    tile_line = int(tile_name[8:12])
    tile_row = int(tile_name[13:17])

    tile_west = tile_name[:8] + '0' + str(tile_line-5) + tile_name[12:]
    tile_east = tile_name[:8] + '0' + str(tile_line+5) + tile_name[12:]
    tile_north = tile_name[:13] + str(tile_row+5) + tile_name[17:]
    tile_south = tile_name[:13] + str(tile_row-5) + tile_name[17:]
    tile_north_west = tile_name[:8] + '0' + str(tile_line-5) + '-' + str(tile_row+5) + tile_name[17:]
    tile_south_west = tile_name[:8] + '0' + str(tile_line-5) + '-' + str(tile_row-5) + tile_name[17:]
    tile_north_east = tile_name[:8] + '0' + str(tile_line+5) + '-' + str(tile_row+5) + tile_name[17:]
    tile_south_east = tile_name[:8] + '0' + str(tile_line+5) + '-' + str(tile_row-5) + tile_name[17:]

    tile_list = [tile_name, tile_west, tile_east, tile_north, tile_south, tile_north_west, tile_south_west, tile_south_west, tile_north_east, tile_south_east]

    final_tile_list = []

    for tile in tiles_geojson["features"]:
        if tile["properties"]["NOM"] in tile_list:
            final_tile_list.append(tile["properties"]["NOM"])
            final_tile_list = list(set(final_tile_list))


filtered_detections = []

'''
## Start detection
'''

run_detection = st.button("DETECT!")
show_heatmap = st.button("HEATMAP")

detections_layer = folium.FeatureGroup(name='detections')

if filtered_detections:
    detections_layer.add_to(m)

def create_heatmap():
    m2 = folium.Map(location=[address_coordinates[0], address_coordinates[1]],
                    zoom_start=15, tiles=final_url, attr='IGN-F/Géoportail', max_zoom=19, min_zoom=15)
    if address_coordinates:
        folium.Marker(location=address_coordinates, tooltip=address).add_to(m2)
        for tile in tiles_geojson["features"]:
            tile_geom = shape(tile["geometry"])

    points = []
    for feature in data['features']:
        points.append(feature['geometry']['coordinates'][::-1])

    heatmap = HeatMap(points, radius=30)

    heatmap.add_to(m2)

    return m2

def create_global_heatmap():
    if address_coordinates:
        center_location = [address_coordinates[0], address_coordinates[1]]
    else:
        center_location = [latitude, longitude]

    m3 = folium.Map(location=center_location,
                    zoom_start=11, tiles=final_url, attr='IGN-F/Géoportail')
    if address_coordinates:
        folium.Marker(location=address_coordinates, tooltip=address).add_to(m3)
        for tile in tiles_geojson["features"]:
            tile_geom = shape(tile["geometry"])

    points = []
    for feature in data['features']:
        points.append(feature['geometry']['coordinates'][::-1])

    heatmap = HeatMap(points, radius=12)

    heatmap.add_to(m3)
    return m3


map_container = st.empty()

if show_heatmap:
    if address_coordinates:
        m2 = create_heatmap()
        marker_cluster = MarkerCluster().add_to(m2)
        folium.ClickForMarker(popup="Add a marker").add_to(m2)
        folium_static(m2, width=1300, height=800)
    else:
        '''
        ### Please enter an address
        '''

elif global_heatmap:
    m3 = create_global_heatmap()
    marker_cluster = MarkerCluster().add_to(m3)
    folium.ClickForMarker(popup="Add a marker").add_to(m3)
    folium_static(m3, width=1300, height=800)


# Si le bouton "DETECT!" est cliqué, afficher la carte principale dans le conteneur vide
else:
    if not address_coordinates and run_detection:
        '''
        ### Please enter an address
        '''
    else: 
        if run_detection and address_coordinates:
            map_container = folium.Map(location=[latitude, longitude], zoom_start=13, tiles=final_url, attr='IGN-F/Géoportail', max_zoom = 19)
            folium.Marker(location=address_coordinates, tooltip=address).add_to(map_container)
            if tile_name:
                for tile in final_tile_list:
                    tile_geom = None
                    for t in tiles_geojson["features"]:
                        if t["properties"]["NOM"] == tile:
                            tile_geom = shape(t["geometry"])
                            break
                    if tile_geom is not None:
                        tile_contour = folium.GeoJson(tile_geom.__geo_interface__, name="tile_contour", style_function=lambda x: {'color': 'red', 'weight': 1, 'fillOpacity': 0})
                        tile_contour.add_to(map_container)

                        for feature in detections_geojson['features']:
                            if feature['properties']['tile'] == tile:
                                filtered_detections.append(feature)
                    
                        if address_coordinates:
                            folium.Marker(location=address_coordinates, tooltip=address).add_to(map_container)
                            map_container.fit_bounds([[address_coordinates[0], address_coordinates[1]]])

                detections_geojson['features'] = filtered_detections

                detections_layer = folium.FeatureGroup(name='detections')
                for detection in detections_geojson["features"]:
                    geojson = folium.GeoJson(
                        detection, 
                        name="detection", 
                        highlight_function=lambda x: {'fillColor': '#ff69b4', 'weight': 8, 'color': 'green', 'fillOpacity': 0.8},
                        tooltip=folium.GeoJsonTooltip(fields=['SURFACE', 'kWp'], aliases=['Surface =', 'kWp =']))
                    geojson.add_to(detections_layer)
                    total_detections += 1
                    total_surface += detection['properties']['SURFACE']
                    total_kWp += detection['properties']['kWp']
                if filtered_detections:
                    detections_layer.add_to(map_container)


            folium.TileLayer(
                    tiles='https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}',
                    attr='Google',
                    name='Google Maps',
                    overlay=True,
                    control=False,
                    max_zoom=16
                ).add_to(map_container)


            marker_cluster = MarkerCluster().add_to(map_container)
            folium.ClickForMarker(popup="Add a marker").add_to(map_container)

            folium.TileLayer('stamentonerlabels', opacity=0.5).add_to(map_container)
            folium_static(map_container, width=1300, height=800)

'''
## Detection Summary : 
'''
if run_detection:
    st.write(f"For a surface of approximately 220 km² around {address}")
    st.write(f"Total Detections: **{total_detections}**")
    st.write(f"Total Surface: **{total_surface:.2f} m²**")
    st.write(f"Total kWp: **{total_kWp:.2f} kWp**")
    
else:
    st.markdown(

    '''
    ### _No detections yet._
    
    <br><br><br><br><br>

    ''', unsafe_allow_html=True
)

st.empty()
st.empty()  
st.empty()
st.empty()
st.empty()
st.markdown(

'''
Merci d'utiliser PanoMapper, une carte de détection plus grande vous sera offerte, dès qu'on arrivera à faire tourner cette VM de mort
'''
)