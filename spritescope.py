# =========================================================
# SPRITESCOPE — STABLE VERSION + TARGET CITY + POLYGON
# =========================================================

import math
import requests
import pandas as pd
import streamlit as st
import folium

from geopy.distance import geodesic
from streamlit_folium import st_folium


# =========================================================
# CONFIG
# =========================================================

st.set_page_config(
    page_title="SpriteScope",
    layout="wide"
)

st.title("⚡ SpriteScope — cône de chasse aux sprites")


# =========================================================
# SESSION
# =========================================================

if "show_polygon" not in st.session_state:
    st.session_state.show_polygon = False


# =========================================================
# FOCALES
# =========================================================

FULL_FRAME = {

    "24 mm": 74,
    "35 mm": 54,
    "50 mm": 40,
    "85 mm": 24,
    "135 mm": 15,
    "200 mm": 10,

}

APS_C = {

    "24 mm": 50,
    "35 mm": 37,
    "50 mm": 27,
    "85 mm": 16,
    "135 mm": 10,
    "200 mm": 7,

}


# =========================================================
# GEOCODAGE
# =========================================================

def geocode_place(query):

    url = "https://nominatim.openstreetmap.org/search"

    params = {

        "q": query,
        "format": "json",
        "limit": 1

    }

    headers = {

        "User-Agent": "SpriteScope"

    }

    try:

        r = requests.get(
            url,
            params=params,
            headers=headers,
            timeout=10
        )

        data = r.json()

        if len(data) > 0:

            lat = float(data[0]["lat"])
            lon = float(data[0]["lon"])

            return lat, lon

    except:
        pass

    return 43.7556, 7.1426


# =========================================================
# PARSE GPS
# =========================================================

def parse_coords(text):

    try:

        text = text.strip()

        text = text.replace("(", "")
        text = text.replace(")", "")

        parts = text.split(",")

        lat = float(parts[0].strip())
        lon = float(parts[1].strip())

        return [lat, lon]

    except:

        return None


# =========================================================
# CALCULS
# =========================================================

def destination_point(lat, lon, bearing, distance_km):

    dest = geodesic(
        kilometers=distance_km
    ).destination(
        (lat, lon),
        bearing
    )

    return (
        dest.latitude,
        dest.longitude
    )


def haversine_km(lat1, lon1, lat2, lon2):

    R = 6371

    p1 = math.radians(lat1)
    p2 = math.radians(lat2)

    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)

    a = (

        math.sin(dp / 2) ** 2

        + math.cos(p1)
        * math.cos(p2)
        * math.sin(dl / 2) ** 2

    )

    return 2 * R * math.atan2(
        math.sqrt(a),
        math.sqrt(1 - a)
    )


def bearing_deg(lat1, lon1, lat2, lon2):

    p1 = math.radians(lat1)
    p2 = math.radians(lat2)

    dl = math.radians(lon2 - lon1)

    x = math.sin(dl) * math.cos(p2)

    y = (

        math.cos(p1)
        * math.sin(p2)

        - math.sin(p1)
        * math.cos(p2)
        * math.cos(dl)

    )

    angle = math.degrees(
        math.atan2(x, y)
    )

    return (angle + 360) % 360


def angle_diff(a, b):

    return abs(
        (a - b + 180) % 360 - 180
    )


def sprite_elevation(
    distance_km,
    altitude_km=80
):

    return math.degrees(
        math.atan(
            altitude_km / distance_km
        )
    )


def in_cone(
    impact_azimuth,
    center_azimuth,
    fov
):

    return (

        angle_diff(
            impact_azimuth,
            center_azimuth
        )

        <= fov / 2

    )


# =========================================================
# IMPACTS TEST
# =========================================================

def get_test_impacts():

    impacts = [

        {"lat": 45.2, "lon": 7.8},
        {"lat": 44.8, "lon": 8.4},
        {"lat": 43.9, "lon": 9.1},
        {"lat": 46.1, "lon": 6.5},
        {"lat": 42.7, "lon": 11.3},
        {"lat": 44.5, "lon": 10.5},
        {"lat": 45.7, "lon": 12.2},
        {"lat": 43.5, "lon": 13.1},
        {"lat": 46.0, "lon": 14.5},

    ]

    return pd.DataFrame(impacts)


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.header("Paramètres")


# =========================================================
# OBSERVATEUR
# =========================================================

lieu = st.sidebar.text_input(
    "Lieu d'observation",
    "Col de Vence"
)


# =========================================================
# MODE VISÉE
# =========================================================

mode_visee = st.sidebar.radio(
    "Mode de visée",
    [
        "Azimut manuel",
        "Ville cible"
    ]
)


# =========================================================
# CAPTEUR
# =========================================================

sensor = st.sidebar.radio(
    "Capteur",
    ["Plein format", "APS-C"]
)


if sensor == "Plein format":
    focales = FULL_FRAME
else:
    focales = APS_C


# =========================================================
# FOCALE
# =========================================================

focale = st.sidebar.selectbox(
    "Focale",
    list(focales.keys()),
    index=2
)

fov = focales[focale]


# =========================================================
# AZIMUT MANUEL OU AUTO
# =========================================================

lat, lon = geocode_place(lieu)

distance_ville = None

if mode_visee == "Azimut manuel":

    azimut = st.sidebar.number_input(
        "Azimut central",
        min_value=0.0,
        max_value=360.0,
        value=150.0,
        step=1.0
    )

else:

    ville_cible = st.sidebar.text_input(
        "Ville cible",
        "Berlin"
    )

    cible_lat, cible_lon = geocode_place(
        ville_cible
    )

    azimut = bearing_deg(
        lat,
        lon,
        cible_lat,
        cible_lon
    )

    distance_ville = haversine_km(
        lat,
        lon,
        cible_lat,
        cible_lon
    )

    st.sidebar.success(
        f"Azimut automatique : {azimut:.1f}°"
    )

    st.sidebar.info(
        f"Distance : {distance_ville:.0f} km"
    )


# =========================================================
# DISTANCE CONE
# =========================================================

distance_cone = st.sidebar.slider(
    "Distance du cône",
    100,
    1000,
    600,
    step=50
)


# =========================================================
# WARNING > 800 KM
# =========================================================

if distance_cone >= 800:

    st.sidebar.warning(
        "⚠️ Au-delà de 800 km, les sprites risquent d’être très bas sur l’horizon."
    )


# =========================================================
# ÉLÉVATION SIDEBAR
# =========================================================

st.sidebar.markdown("---")
st.sidebar.markdown("## Élévation sprite")

st.sidebar.markdown(

    f"""

200 km → {sprite_elevation(200):.1f}°  

400 km → {sprite_elevation(400):.1f}°  

600 km → {sprite_elevation(600):.1f}°  

800 km → {sprite_elevation(800):.1f}°

"""

)


# =========================================================
# ORAGE POLYGONE
# =========================================================

st.sidebar.markdown("---")
st.sidebar.markdown("## Coordonnées éclairs")


left_text = st.sidebar.text_input(
    "⚡ Éclair gauche",
    "49.99, -3.86"
)

center_text = st.sidebar.text_input(
    "⚡ Éclair centre",
    "50.10, -2.90"
)

right_text = st.sidebar.text_input(
    "⚡ Éclair droite",
    "50.20, -1.80"
)


use_extra = st.sidebar.checkbox(
    "Ajouter proche / éloigné",
    value=False
)

if use_extra:

    near_text = st.sidebar.text_input(
        "⚡ Éclair le plus proche",
        "49.80, -2.70"
    )

    far_text = st.sidebar.text_input(
        "⚡ Éclair le plus éloigné",
        "50.50, -2.60"
    )


if st.sidebar.button(
    "Générer polygone simulation orage"
):
    st.session_state.show_polygon = True


if st.sidebar.button(
    "Effacer polygone"
):
    st.session_state.show_polygon = False


# =========================================================
# IMPACTS
# =========================================================

impacts = get_test_impacts()

distances = []
azimuths = []
elevations = []
inside = []


for _, row in impacts.iterrows():

    d = haversine_km(
        lat,
        lon,
        row["lat"],
        row["lon"]
    )

    az = bearing_deg(
        lat,
        lon,
        row["lat"],
        row["lon"]
    )

    el = sprite_elevation(d)

    ok = in_cone(
        az,
        azimut,
        fov
    )

    distances.append(d)
    azimuths.append(az)
    elevations.append(el)
    inside.append(ok)


impacts["distance_km"] = distances
impacts["azimuth"] = azimuths
impacts["elevation"] = elevations
impacts["inside"] = inside


# =========================================================
# INFOS
# =========================================================

st.write(
    f"📍 {lieu} — "
    f"{lat:.5f}, {lon:.5f}"
)

if distance_ville is not None:

    st.write(
        f"🎯 Ville cible : {ville_cible}"
    )

    st.write(
        f"📏 Distance : {distance_ville:.0f} km"
    )

st.write(
    f"📷 {sensor} — "
    f"{focale} — "
    f"champ horizontal : {fov}°"
)

st.write(
    f"🧭 cône : "
    f"{azimut - fov/2:.1f}° "
    f"→ "
    f"{azimut + fov/2:.1f}°"
)


# =========================================================
# CARTE CLAIRE
# =========================================================

m = folium.Map(
    location=[lat, lon],
    zoom_start=6,
    tiles="CartoDB positron"
)


# =========================================================
# OBSERVATEUR
# =========================================================

folium.Marker(

    [lat, lon],

    popup=lieu,

    icon=folium.Icon(
        color="purple"
    )

).add_to(m)


# =========================================================
# VILLE CIBLE
# =========================================================

if mode_visee == "Ville cible":

    folium.Marker(

        [cible_lat, cible_lon],

        popup=ville_cible,

        icon=folium.Icon(
            color="red"
        )

    ).add_to(m)


# =========================================================
# CONE
# =========================================================

left_az = azimut - fov / 2
right_az = azimut + fov / 2


left_point = destination_point(
    lat,
    lon,
    left_az,
    distance_cone
)

center_point = destination_point(
    lat,
    lon,
    azimut,
    distance_cone
)

right_point = destination_point(
    lat,
    lon,
    right_az,
    distance_cone
)


folium.Polygon(

    [
        [lat, lon],
        left_point,
        center_point,
        right_point
    ],

    color="purple",
    fill=True,
    fill_opacity=0.15

).add_to(m)


# =========================================================
# PARSE ECLAIRS
# =========================================================

left_coords = parse_coords(left_text)
center_coords = parse_coords(center_text)
right_coords = parse_coords(right_text)

display_points = []
polygon_points = []


if left_coords:
    display_points.append(left_coords)

if center_coords:
    display_points.append(center_coords)

if right_coords:
    display_points.append(right_coords)


# =========================================================
# POLYGONE ORAGE
# =========================================================

if use_extra:

    near_coords = parse_coords(near_text)
    far_coords = parse_coords(far_text)

    if near_coords:
        display_points.append(near_coords)

    if far_coords:
        display_points.append(far_coords)

    if left_coords:
        polygon_points.append(left_coords)

    if near_coords:
        polygon_points.append(near_coords)

    if right_coords:
        polygon_points.append(right_coords)

    if far_coords:
        polygon_points.append(far_coords)

else:

    if left_coords:
        polygon_points.append(left_coords)

    if center_coords:
        polygon_points.append(center_coords)

    if right_coords:
        polygon_points.append(right_coords)


# =========================================================
# AFFICHAGE ECLAIRS
# =========================================================

for point in display_points:

    folium.Marker(

        point,

        icon=folium.DivIcon(

            html="""
            <div style="
                font-size:26px;
                color:red;
                text-shadow:0 0 6px white;
            ">
            ⚡
            </div>
            """

        )

    ).add_to(m)


# =========================================================
# POLYGONE
# =========================================================

if st.session_state.show_polygon and len(polygon_points) >= 3:

    folium.Polygon(

        polygon_points,

        color="red",

        weight=3,

        fill=True,

        fill_opacity=0.20

    ).add_to(m)


# =========================================================
# IMPACTS
# =========================================================

for _, row in impacts.iterrows():

    color = (
        "red"
        if row["inside"]
        else "white"
    )

    popup = (

        f"Distance : "
        f"{row['distance_km']:.0f} km<br>"

        f"Azimut : "
        f"{row['azimuth']:.1f}°<br>"

        f"Élévation sprite : "
        f"{row['elevation']:.1f}°"

    )

    folium.CircleMarker(

        [row["lat"], row["lon"]],

        radius=6,

        color=color,

        fill=True,

        fill_opacity=0.9,

        popup=popup

    ).add_to(m)


# =========================================================
# AFFICHAGE CARTE
# =========================================================

map_data = st_folium(

    m,

    height=750,

    width=None,

    returned_objects=["last_clicked"]

)


# =========================================================
# DÉPLACEMENT SPOT
# =========================================================

if map_data["last_clicked"]:

    st.session_state.lat = map_data["last_clicked"]["lat"]
    st.session_state.lon = map_data["last_clicked"]["lng"]

    st.rerun()


# =========================================================
# TABLEAU IMPACTS
# =========================================================

st.subheader("Impacts")

st.dataframe(

    impacts[

        [
            "distance_km",
            "azimuth",
            "elevation",
            "inside"
        ]

    ],

    use_container_width=True

)


# =========================================================
# FOOTER
# =========================================================

st.markdown("---")

st.markdown("""

### SpriteScope  
Conçu par **Sylvain Reybaut** © 2026 — Tous droits réservés.

Pour en savoir plus sur les sprites :  
http://www.reybaut.fr

Instagram :  
https://www.instagram.com/sylvain.reybaut/

""")
