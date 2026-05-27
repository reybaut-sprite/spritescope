import math
import requests
import streamlit as st
import folium
import urllib3

from geopy.distance import geodesic
from streamlit_folium import st_folium


# =========================================================
# SSL FIX FOR STREAMLIT CLOUD
# =========================================================

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


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
    ["English", "Français"],
    index=1
)

EN = language == "English"


def tr(en, fr):
    return en if EN else fr


# =========================================================
# TITLE
# =========================================================

st.title(
    tr(
        "⚡ SpriteScope — Storm polygon mode",
        "⚡ SpriteScope — Mode polygone orage"
    )
)


# =========================================================
# FOCAL DATABASE
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
        "User-Agent": "Mozilla/5.0"
    }

    try:

        r = requests.get(
            url,
            params=params,
            headers=headers,
            timeout=10,
            verify=False
        )

        data = r.json()

        if len(data) > 0:

            lat = float(data[0]["lat"])
            lon = float(data[0]["lon"])

            return lat, lon

    except:
        pass

    # fallback Monaco
    return 43.7384, 7.4246


# =========================================================
# DISTANCE
# =========================================================

def haversine(lat1, lon1, lat2, lon2):

    R = 6371

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)

    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = (

        math.sin(dphi / 2) ** 2

        + math.cos(phi1)
        * math.cos(phi2)
        * math.sin(dlambda / 2) ** 2

    )

    return 2 * R * math.atan2(
        math.sqrt(a),
        math.sqrt(1 - a)
    )


# =========================================================
# AZIMUTH
# =========================================================

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
# DESTINATION POINT
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
# SPRITE ELEVATION
# =========================================================

def sprite_elevation(distance_km, sprite_height=70):

    angle = math.degrees(
        math.atan(sprite_height / distance_km)
    )

    return round(angle, 1)


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
    "Monaco"
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
# FOCAL
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
# TARGET CITY
# =========================================================

distance_villes = None

if mode_visee == tr("Target city", "Ville cible"):

    ville_cible = st.sidebar.text_input(
        tr(
            "Target city",
            "Ville cible"
        ),
        "Ljubljana"
    )

    cible_lat, cible_lon = geocode_place(ville_cible)

    azimut = bearing_deg(
        lat,
        lon,
        cible_lat,
        cible_lon
    )

    distance_villes = haversine(
        lat,
        lon,
        cible_lat,
        cible_lon
    )

    st.sidebar.success(
        f"Azimuth : {azimut:.1f}°"
    )

    st.sidebar.info(
        f"Distance : {distance_villes:.0f} km"
    )

else:

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
# CONE DISTANCE
# =========================================================

distance_cone = st.sidebar.slider(
    tr(
        "Cone distance",
        "Distance du cône"
    ),
    100,
    1500,
    600,
    step=50
)


# =========================================================
# SPRITE TABLE
# =========================================================

st.sidebar.markdown("---")

st.sidebar.subheader(
    tr(
        "Sprite elevation table",
        "Tableau élévation sprites"
    )
)

table_data = {

    tr("Distance", "Distance"):
        ["200 km", "400 km", "600 km", "800 km"],

    tr(
        "Elevation angle",
        "Angle élévation"
    ):
        [
            f"{sprite_elevation(200)}°",
            f"{sprite_elevation(400)}°",
            f"{sprite_elevation(600)}°",
            f"{sprite_elevation(800)}°"
        ]

}

st.sidebar.table(table_data)


# =========================================================
# WARNING
# =========================================================

if distance_cone >= 800:

    st.sidebar.warning(

        tr(
            "⚠️ Beyond 800 km, sprites may appear very low on the horizon.",
            "⚠️ Au-delà de 800 km, les sprites risquent d’être très bas sur l’horizon."
        )

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

left_text = st.sidebar.text_input(
    tr(
        "⚡ Left lightning",
        "⚡ Éclair gauche"
    ),
    "49.99, -3.86"
)

center_text = st.sidebar.text_input(
    tr(
        "⚡ Center lightning",
        "⚡ Éclair centre"
    ),
    "50.10, -2.90"
)

right_text = st.sidebar.text_input(
    tr(
        "⚡ Right lightning",
        "⚡ Éclair droite"
    ),
    "50.20, -1.80"
)


# =========================================================
# FRONT / BACK
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
# INFOS
# =========================================================

st.write(f"📍 {lieu} — {lat:.5f}, {lon:.5f}")

st.write(
    f"📷 {sensor} — {focale} — "
    f"{tr('horizontal field', 'champ horizontal')} : {fov}°"
)

st.write(f"🧭 Azimuth : {azimut:.1f}°")

st.write(
    f"🎯 Cone : "
    f"{azimut - fov / 2:.1f}° → "
    f"{azimut + fov / 2:.1f}°"
)

if distance_villes is not None:

    st.write(
        f"📏 {tr('Distance between cities', 'Distance entre les deux villes')} : "
        f"{distance_villes:.0f} km"
    )


# =========================================================
# MAP
# =========================================================

m = folium.Map(
    location=[lat, lon],
    zoom_start=5,
    tiles="CartoDB positron"
)


# =========================================================
# OBSERVER MARKER
# =========================================================

folium.Marker(
    [lat, lon],
    popup=lieu,
    icon=folium.Icon(color="purple")
).add_to(m)


# =========================================================
# TARGET CITY MARKER
# =========================================================

if mode_visee == tr("Target city", "Ville cible"):

    folium.Marker(
        [cible_lat, cible_lon],
        popup=ville_cible,
        icon=folium.Icon(color="red")
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

folium.PolyLine(
    [
        [lat, lon],
        center_point
    ],
    color="purple",
    weight=2,
    dash_array="5"
).add_to(m)


# =========================================================
# STORM POINTS
# =========================================================

left_coords = parse_coords(left_text)
center_coords = parse_coords(center_text)
right_coords = parse_coords(right_text)

storm_points = []
display_points = []

if left_coords:
    display_points.append(left_coords)

if center_coords:
    display_points.append(center_coords)

if right_coords:
    display_points.append(right_coords)


if use_extra:

    front_coords = parse_coords(front_text)
    back_coords = parse_coords(back_text)

    if front_coords:
        display_points.append(front_coords)

    if back_coords:
        display_points.append(back_coords)

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
# LIGHTNING DISPLAY
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
# STORM POLYGON
# =========================================================

if st.session_state.show_polygon and len(storm_points) >= 3:

    folium.Polygon(

        storm_points,

        color="red",

        weight=3,

        fill=True,

        fill_opacity=0.20

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

st.markdown(

    tr(

        """
        **SpriteScope**  
        Designed by Sylvain Reybaut © 2026 — All rights reserved.

        This application is intended as a visual aid for sprite hunting.

        Sprite occurrence can never be guaranteed.
        """,

        """
        **SpriteScope**  
        Conçu par Sylvain Reybaut © 2026 — Tous droits réservés.

        Cette application est une aide visuelle à la chasse aux sprites.

        L’apparition des sprites ne peut jamais être garantie.

        Pour en savoir plus sur les reds sprite, rendez vous sur
        http://www.reybaut.fr
        Follow me sur insta : https://www.instagram.com/sylvain.reybaut/
        
        """

    )

)
