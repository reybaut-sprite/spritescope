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


st.title(
    tr(
        "⚡ SpriteScope — sprite hunting cone",
        "⚡ SpriteScope — cône de chasse aux sprites"
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
    altitude_km
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
# LIGHTNING IMPACTS
# =========================================================

def get_real_lightning():

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

st.sidebar.header(
    tr(
        "Settings",
        "Paramètres"
    )
)


# =========================================================
# OBSERVER
# =========================================================

lieu = st.sidebar.text_input(

    tr(
        "Observation location",
        "Lieu d'observation"
    ),

    "Col de Vence"

)


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
# OBSERVER POSITION
# =========================================================

if "lat" not in st.session_state:

    default_lat, default_lon = geocode_place(lieu)

    st.session_state.lat = default_lat
    st.session_state.lon = default_lon


if "last_place" not in st.session_state:

    st.session_state.last_place = lieu


if lieu != st.session_state.last_place:

    new_lat, new_lon = geocode_place(lieu)

    st.session_state.lat = new_lat
    st.session_state.lon = new_lon

    st.session_state.last_place = lieu


lat = st.session_state.lat
lon = st.session_state.lon


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
# AZIMUTH
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

    distance_ville = None


else:

    ville_cible = st.sidebar.text_input(

        tr(
            "Target city",
            "Ville cible"
        ),

        "Ljubljana"

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
        f"Azimuth : {azimut:.1f}°"
    )

    st.sidebar.success(
        f"Distance : {distance_ville:.0f} km"
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
    1000,
    600,
    step=50

)


# =========================================================
# SPRITE HEIGHT
# =========================================================

niveau_sprite = st.sidebar.radio(

    tr(
        "Sprite height",
        "Hauteur du sprite"
    ),

    [
        tr("Bottom", "Bas"),
        tr("Middle", "Milieu"),
        tr("Top", "Sommet")
    ],

    index=1

)

if niveau_sprite == tr("Bottom", "Bas"):

    altitude_sprite = 50

elif niveau_sprite == tr("Middle", "Milieu"):

    altitude_sprite = 75

else:

    altitude_sprite = 90


# =========================================================
# MOVE MODE
# =========================================================

move_mode = st.sidebar.checkbox(

    tr(
        "Move spot manually",
        "Déplacer le spot manuellement"
    ),

    value=False

)

if move_mode:

    st.sidebar.info(

        tr(
            "Click on the map to move the spot.",
            "Cliquez sur la carte pour déplacer le spot."
        )

    )


# =========================================================
# VISIBILITY WARNINGS
# =========================================================

if mode_visee == tr("Target city", "Ville cible"):

    if distance_ville > 800:

        st.error(

            tr(
                "⚠️ Warning: beyond 800 km, low sprites may fall below the horizon.",
                "⚠️ Attention : au-delà de 800 km, les sprites bas peuvent passer sous l’horizon."
            )

        )

    elif distance_ville > 650:

        st.warning(

            tr(
                "⚠️ Long distance: low sprites will be harder to see.",
                "⚠️ Distance importante : les sprites bas seront plus difficiles à voir."
            )

        )

    else:

        st.success(

            tr(
                "✅ Favorable distance for sprite visibility.",
                "✅ Distance favorable pour la visibilité des sprites."
            )

        )


# =========================================================
# LIGHTNING
# =========================================================

impacts = get_real_lightning()

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

    el = sprite_elevation(
        d,
        altitude_sprite
    )

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
# INFO
# =========================================================

st.write(
    f"📍 {lieu} — "
    f"{lat:.5f}, {lon:.5f}"
)

st.write(
    f"📷 {sensor} — "
    f"{focale} — "
    f"{tr('horizontal field', 'champ horizontal')} : "
    f"{fov}°"
)

st.write(
    f"🧭 "
    f"{azimut - fov/2:.1f}° "
    f"→ "
    f"{azimut + fov/2:.1f}°"
)

st.write(
    f"⚡ "
    f"{niveau_sprite} "
    f"({altitude_sprite} km)"
)


# =========================================================
# SPRITE ELEVATION TABLE
# =========================================================

elev_200 = sprite_elevation(200, altitude_sprite)
elev_300 = sprite_elevation(300, altitude_sprite)
elev_400 = sprite_elevation(400, altitude_sprite)
elev_500 = sprite_elevation(500, altitude_sprite)
elev_600 = sprite_elevation(600, altitude_sprite)

st.sidebar.markdown("---")

st.sidebar.markdown(
    tr(
        "## Sprite elevation",
        "## Élévation sprite"
    )
)

st.sidebar.markdown(

    f"""

200 km → {elev_200:.1f}°  

300 km → {elev_300:.1f}°  

400 km → {elev_400:.1f}°  

500 km → {elev_500:.1f}°  

600 km → {elev_600:.1f}°

"""

)


# =========================================================
# MAP
# =========================================================

m = folium.Map(
    location=[lat, lon],
    zoom_start=6,
    tiles="CartoDB positron"
)


# =========================================================
# REAL LIGHTNING LAYER
# =========================================================

folium.TileLayer(

    tiles=(
        "https://tiles.lightningmaps.org/"
        "tiles/"
        "lightning_brt/"
        "{z}/{x}/{y}.png"
    ),

    attr="LightningMaps",

    name="Lightning",

    overlay=True,

    control=True

).add_to(m)


# =========================================================
# OBSERVER MARKER
# =========================================================

folium.Marker(

    [lat, lon],

    popup="Observer",

    icon=folium.Icon(
        color="purple"
    )

).add_to(m)


folium.CircleMarker(

    [lat, lon],

    radius=12,

    color="cyan",

    fill=True,

    fill_opacity=0.35

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
    [[lat, lon], left_point],
    color="purple",
    weight=3
).add_to(m)

folium.PolyLine(
    [[lat, lon], right_point],
    color="purple",
    weight=3
).add_to(m)

folium.PolyLine(
    [[lat, lon], center_point],
    color="black",
    weight=1,
    dash_array="5"
).add_to(m)


folium.Circle(
    location=[lat, lon],
    radius=distance_cone * 1000,
    color="black",
    weight=1,
    opacity=0.25,
    fill=False
).add_to(m)


# =========================================================
# TARGET CITY
# =========================================================

if mode_visee == tr("Target city", "Ville cible"):

    folium.Marker(

        [cible_lat, cible_lon],

        popup=ville_cible,

        icon=folium.Icon(
            color="red"
        )

    ).add_to(m)


# =========================================================
# LOCAL IMPACTS
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

        f"Azimuth : "
        f"{row['azimuth']:.1f}°<br>"

        f"Sprite elevation : "
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
# LAYER CONTROL
# =========================================================

folium.LayerControl().add_to(m)


# =========================================================
# MAP DISPLAY
# =========================================================

map_data = st_folium(

    m,

    height=750,

    width=None,

    returned_objects=["last_clicked"]

)


# =========================================================
# MOVE SPOT
# =========================================================

if move_mode:

    if map_data["last_clicked"]:

        st.session_state.lat = map_data["last_clicked"]["lat"]
        st.session_state.lon = map_data["last_clicked"]["lng"]

        st.rerun()


# =========================================================
# TABLE
# =========================================================

st.subheader(
    tr(
        "Lightning strikes",
        "Impacts"
    )
)

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