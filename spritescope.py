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

lat, lon = geocode_place(lieu)


# =========================================================
# VILLE CIBLE
# =========================================================

ville_cible = st.sidebar.text_input(
    "Ville cible",
    "Ljubljana"
)

cible_lat, cible_lon = geocode_place(
    ville_cible
)


# =========================================================
# DISTANCE + AZIMUT
# =========================================================

distance_ville = haversine_km(
    lat,
    lon,
    cible_lat,
    cible_lon
)

azimut = bearing_deg(
    lat,
    lon,
    cible_lat,
    cible_lon
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
# DISTANCE CONE
# =========================================================

distance_cone = st.sidebar.slider(
    "Distance du cône",
    100,
    1200,
    600,
    step=50
)


# =========================================================
# ORAGE
# =========================================================

st.sidebar.markdown("---")

st.sidebar.markdown("## Coordonnées éclairs")


left_text = st.sidebar.text_input(
    "⚡ Éclair le plus à gauche",
    "49.99, -3.86"
)

center_text = st.sidebar.text_input(
    "⚡ Éclair central",
    "50.10, -2.90"
)

right_text = st.sidebar.text_input(
    "⚡ Éclair le plus à droite",
    "50.20, -1.80"
)


# =========================================================
# OPTION PROCHE / LOINTAIN
# =========================================================

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


# =========================================================
# BOUTONS
# =========================================================

if st.sidebar.button(
    "Générer polygone simulation orage"
):
    st.session_state.show_polygon = True


if st.sidebar.button(
    "Effacer polygone"
):
    st.session_state.show_polygon = False


# =========================================================
# INFOS
# =========================================================

st.write(
    f"📍 {lieu} — "
    f"{lat:.5f}, {lon:.5f}"
)

st.write(
    f"🎯 Ville cible : "
    f"{ville_cible}"
)

st.write(
    f"📏 Distance : "
    f"{distance_ville:.0f} km"
)

st.write(
    f"🧭 Azimut : "
    f"{azimut:.1f}°"
)

st.write(
    f"📷 {sensor} — "
    f"{focale} — "
    f"champ horizontal : {fov}°"
)

st.write(
    f"🎯 cône : "
    f"{azimut - fov/2:.1f}° "
    f"→ "
    f"{azimut + fov/2:.1f}°"
)


# =========================================================
# CARTE CLAIRE
# =========================================================

m = folium.Map(
    location=[lat, lon],
    zoom_start=5,
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
# ORDRE POLYGONE
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
# POLYGONE ORAGE
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
# AFFICHAGE CARTE
# =========================================================

st_folium(

    m,

    height=750,

    width=None

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
