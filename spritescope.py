# =========================================================
# SPRITESCOPE — FINAL HYBRID VERSION
# =========================================================

import math
import requests
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


# =========================================================
# SESSION STATE
# =========================================================

if "show_polygon" not in st.session_state:
    st.session_state.show_polygon = False


# =========================================================
# LANGUAGE
# =========================================================

language = st.sidebar.radio(

    "Language",

    [
        "English",
        "Français"
    ],

    index=0

)

EN = language == "English"


def tr(en, fr):

    if EN:
        return en

    return fr


# =========================================================
# TITLE
# =========================================================

st.title(
    tr(
        "⚡ SpriteScope — Storm polygon mode",
        "⚡ SpriteScope — mode polygone orageux"
    )
)


# =========================================================
# FOCAL LENGTHS
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
# GEOCODING
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
# PARSE GPS COORDS
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
# CALCULATIONS
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

st.sidebar.header(
    tr(
        "Settings",
        "Paramètres"
    )
)


# =========================================================
# OBSERVER LOCATION
# =========================================================

lieu = st.sidebar.text_input(

    tr(
        "Observation location",
        "Lieu d'observation"
    ),

    "Col de Vence"

)

lat, lon = geocode_place(lieu)


# =========================================================
# SENSOR
# =========================================================

sensor = st.sidebar.radio(

    tr(
        "Sensor",
        "Capteur"
    ),

    [
        tr("Full frame", "Plein format"),
        "APS-C"
    ]

)

if sensor == tr("Full frame", "Plein format"):
    focales = FULL_FRAME
else:
    focales = APS_C


# =========================================================
# FOCAL LENGTH
# =========================================================

focale = st.sidebar.selectbox(

    tr(
        "Focal length",
        "Focale"
    ),

    list(focales.keys()),

    index=2

)

fov = focales[focale]


# =========================================================
# TARGET MODE
# =========================================================

mode_visee = st.sidebar.radio(

    tr(
        "Target mode",
        "Mode de visée"
    ),

    [
        tr("Manual azimuth", "Azimut manuel"),
        tr("Target city", "Ville cible")
    ]

)


# =========================================================
# MANUAL AZIMUTH
# =========================================================

if mode_visee == tr("Manual azimuth", "Azimut manuel"):

    azimut = st.sidebar.number_input(

        tr(
            "Central azimuth",
            "Azimut central"
        ),

        min_value=0.0,
        max_value=360.0,

        value=150.0,

        step=1.0

    )


# =========================================================
# TARGET CITY
# =========================================================

else:

    ville_cible = st.sidebar.text_input(

        tr(
            "Target city",
            "Ville cible"
        ),

        "London"

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

    st.sidebar.success(
        f"Azimuth : {azimut:.1f}°"
    )


# =========================================================
# CONE DISTANCE
# =========================================================

distance_cone = st.sidebar.slider(

    tr(
        "Cone distance",
        "Distance du cône"
    ),

    100,
    1200,
    600,
    step=50

)


# =========================================================
# STORM INPUTS
# =========================================================

st.sidebar.markdown("---")

st.sidebar.subheader(
    tr(
        "Storm lightning coordinates",
        "Coordonnées éclairs orage"
    )
)


# =========================================================
# LEFT
# =========================================================

left_text = st.sidebar.text_input(

    tr(
        "⚡ Left lightning",
        "⚡ Éclair gauche"
    ),

    "49.99, -3.86"

)


# =========================================================
# CENTER
# =========================================================

center_text = st.sidebar.text_input(

    tr(
        "⚡ Center lightning",
        "⚡ Éclair centre"
    ),

    "50.10, -2.90"

)


# =========================================================
# RIGHT
# =========================================================

right_text = st.sidebar.text_input(

    tr(
        "⚡ Right lightning",
        "⚡ Éclair droite"
    ),

    "50.20, -1.80"

)


# =========================================================
# OPTIONAL FRONT / BACK
# =========================================================

use_extra = st.sidebar.checkbox(

    tr(
        "Use front / back points",
        "Utiliser avant / arrière"
    ),

    value=False

)


if use_extra:

    front_text = st.sidebar.text_input(

        tr(
            "⚡ Front lightning",
            "⚡ Éclair avant"
        ),

        "50.40, -2.40"

    )

    back_text = st.sidebar.text_input(

        tr(
            "⚡ Back lightning",
            "⚡ Éclair arrière"
        ),

        "49.70, -2.50"

    )


# =========================================================
# BUTTONS
# =========================================================

if st.sidebar.button(

    tr(
        "Generate storm polygon",
        "Générer cellule orageuse"
    )

):

    st.session_state.show_polygon = True


if st.sidebar.button(

    tr(
        "Clear polygon",
        "Effacer polygone"
    )

):

    st.session_state.show_polygon = False


# =========================================================
# MAP
# =========================================================

m = folium.Map(
    location=[lat, lon],
    zoom_start=5,
    tiles="CartoDB positron"
)


# =========================================================
# OBSERVER
# =========================================================

folium.Marker(

    [lat, lon],

    popup="Observer",

    icon=folium.Icon(
        color="purple"
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
# PARSE LIGHTNING POINTS
# =========================================================

left_coords = parse_coords(left_text)
center_coords = parse_coords(center_text)
right_coords = parse_coords(right_text)

storm_points = []


# =========================================================
# POLYGON ORDER
# =========================================================

if use_extra:

    front_coords = parse_coords(front_text)
    back_coords = parse_coords(back_text)

    if left_coords:
        storm_points.append(left_coords)

    if back_coords:
        storm_points.append(back_coords)

    if right_coords:
        storm_points.append(right_coords)

    if front_coords:
        storm_points.append(front_coords)

else:

    if left_coords:
        storm_points.append(left_coords)

    if center_coords:
        storm_points.append(center_coords)

    if right_coords:
        storm_points.append(right_coords)


# =========================================================
# DISPLAY LIGHTNING
# =========================================================

for point in storm_points:

    folium.Marker(

        point,

        icon=folium.DivIcon(

            html="""
            <div style="
                font-size:24px;
                color:red;
                text-shadow:0 0 6px white;
            ">
            ⚡
            </div>
            """

        )

    ).add_to(m)


# =========================================================
# STORM POLYGON
# =========================================================

if st.session_state.show_polygon and len(storm_points) >= 3:

    folium.Polygon(

        storm_points,

        color="red",

        weight=3,

        fill=True,

        fill_opacity=0.18

    ).add_to(m)


# =========================================================
# DISPLAY MAP
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

if EN:

    st.markdown("""

**SpriteScope**  
Designed by Sylvain Reybaut © 2026 — All rights reserved.

This application is intended as a visual and educational aid for sprite hunting.

Sprite occurrence can never be guaranteed.

""")

else:

    st.markdown("""

**SpriteScope**  
Conçu par Sylvain Reybaut © 2026 — Tous droits réservés.

Cette application est une aide visuelle et éducative à la chasse aux sprites.

L’apparition des sprites ne peut jamais être garantie.

""")