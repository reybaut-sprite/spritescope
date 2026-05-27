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
# VILLES CONNUES — SÉCURITÉ
# =========================================================

KNOWN_PLACES = {
    "col de vence": (43.7556, 7.1426),
    "vence": (43.7220, 7.1138),
    "nice": (43.7102, 7.2620),
    "monaco": (43.7384, 7.4246),
    "paris": (48.8566, 2.3522),
    "brest": (48.3904, -4.4861),
    "strasbourg": (48.5734, 7.7521),
    "ljubljana": (46.0569, 14.5058),
    "lubjana": (46.0569, 14.5058),
    "londres": (51.5072, -0.1276),
    "london": (51.5072, -0.1276),
    "barcelone": (41.3851, 2.1734),
    "barcelona": (41.3851, 2.1734),
    "milan": (45.4642, 9.1900),
    "milano": (45.4642, 9.1900),
}


# =========================================================
# GEOCODAGE
# =========================================================

def geocode_place(query):

    q = query.strip().lower()

    if q in KNOWN_PLACES:
        return KNOWN_PLACES[q]

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
# CALCULS
# =========================================================

def destination_point(lat, lon, bearing, distance_km):

    dest = geodesic(
        kilometers=distance_km
    ).destination(
        (lat, lon),
        bearing
    )

    return dest.latitude, dest.longitude


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


def sprite_elevation(distance_km, altitude_km=75):

    return math.degrees(
        math.atan(
            altitude_km / distance_km
        )
    )


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
# SIDEBAR
# =========================================================

st.sidebar.header("Paramètres")


lieu = st.sidebar.text_input(
    "Lieu d'observation",
    "Col de Vence"
)


sensor = st.sidebar.radio(
    "Capteur",
    ["Plein format", "APS-C"]
)


if sensor == "Plein format":
    focales = FULL_FRAME
else:
    focales = APS_C


focale = st.sidebar.selectbox(
    "Focale",
    list(focales.keys()),
    index=2
)


fov = focales[focale]


# =========================================================
# POSITION OBSERVATEUR
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
# MODE DE VISÉE
# =========================================================

mode_visee = st.sidebar.radio(
    "Mode de visée",
    ["Azimut manuel", "Ville cible"]
)


distance_ville = None
ville_cible = None
cible_lat = None
cible_lon = None


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
        "Ljubljana"
    )

    cible_lat, cible_lon = geocode_place(ville_cible)

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
        f"Azimut : {azimut:.1f}°"
    )

    st.sidebar.info(
        f"Distance : {distance_ville:.0f} km"
    )

    if distance_ville >= 800:
        st.sidebar.warning(
            "⚠️ Au-delà de 800 km, les sprites risquent d’être très bas sur l’horizon."
        )


distance_cone = st.sidebar.slider(
    "Distance du cône",
    100,
    1500,
    600,
    step=50
)


niveau_sprite = st.sidebar.radio(
    "Hauteur du sprite",
    ["Bas", "Milieu", "Sommet"],
    index=1
)

if niveau_sprite == "Bas":
    altitude_sprite = 50

elif niveau_sprite == "Milieu":
    altitude_sprite = 75

else:
    altitude_sprite = 90


# =========================================================
# TABLEAU ÉLÉVATION SIDEBAR
# =========================================================

st.sidebar.markdown("---")

st.sidebar.markdown("## Élévation sprite")

st.sidebar.markdown(
    f"""
200 km → {sprite_elevation(200, altitude_sprite):.1f}°  

400 km → {sprite_elevation(400, altitude_sprite):.1f}°  

600 km → {sprite_elevation(600, altitude_sprite):.1f}°  

800 km → {sprite_elevation(800, altitude_sprite):.1f}°
"""
)

if distance_cone >= 800:
    st.sidebar.warning(
        "⚠️ Distance du cône ≥ 800 km : sprites possiblement très bas sur l’horizon."
    )


# =========================================================
# COORDONNÉES ÉCLAIRS ORAGE
# =========================================================

st.sidebar.markdown("---")
st.sidebar.markdown("## Coordonnées éclairs orage")

left_text = st.sidebar.text_input(
    "⚡ Éclair gauche",
    "49.99, -3.86"
)

center_text = st.sidebar.text_input(
    "⚡ Éclair milieu",
    "50.10, -2.90"
)

right_text = st.sidebar.text_input(
    "⚡ Éclair droite",
    "50.20, -1.80"
)


use_extra = st.sidebar.checkbox(
    "Ajouter avant / arrière",
    value=False
)

if use_extra:

    front_text = st.sidebar.text_input(
        "⚡ Éclair avant",
        "50.40, -2.40"
    )

    back_text = st.sidebar.text_input(
        "⚡ Éclair arrière",
        "49.70, -2.50"
    )


if st.sidebar.button("Générer polygone orageux"):
    st.session_state.show_polygon = True


if st.sidebar.button("Effacer polygone"):
    st.session_state.show_polygon = False


# =========================================================
# INFOS
# =========================================================

st.write(
    f"📍 {lieu} — "
    f"{lat:.5f}, {lon:.5f}"
)

st.write(
    f"📷 {sensor} — "
    f"{focale} — "
    f"champ horizontal : {fov}°"
)

st.write(
    f"🧭 azimut : {azimut:.1f}°"
)

st.write(
    f"🎯 cône : "
    f"{azimut - fov/2:.1f}° "
    f"→ "
    f"{azimut + fov/2:.1f}°"
)

if distance_ville is not None:

    st.write(
        f"📏 Distance entre {lieu} et {ville_cible} : "
        f"{distance_ville:.0f} km"
    )


# =========================================================
# CARTE
# =========================================================

m = folium.Map(
    location=[lat, lon],
    zoom_start=6,
    tiles="CartoDB positron"
)


# OBSERVATEUR

folium.Marker(
    [lat, lon],
    popup=lieu,
    icon=folium.Icon(color="purple")
).add_to(m)


# VILLE CIBLE

if mode_visee == "Ville cible":

    folium.Marker(
        [cible_lat, cible_lon],
        popup=ville_cible,
        icon=folium.Icon(color="red")
    ).add_to(m)


# CÔNE

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
# POINTS ÉCLAIRS
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


if use_extra:

    front_coords = parse_coords(front_text)
    back_coords = parse_coords(back_text)

    if front_coords:
        display_points.append(front_coords)

    if back_coords:
        display_points.append(back_coords)

    if left_coords:
        polygon_points.append(left_coords)

    if back_coords:
        polygon_points.append(back_coords)

    if right_coords:
        polygon_points.append(right_coords)

    if front_coords:
        polygon_points.append(front_coords)

else:

    if left_coords:
        polygon_points.append(left_coords)

    if center_coords:
        polygon_points.append(center_coords)

    if right_coords:
        polygon_points.append(right_coords)


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

map_data = st_folium(
    m,
    height=750,
    width=None,
    returned_objects=["last_clicked"]
)


# =========================================================
# DÉPLACEMENT SPOT PAR CLIC
# =========================================================

if map_data["last_clicked"]:

    st.session_state.lat = map_data["last_clicked"]["lat"]
    st.session_state.lon = map_data["last_clicked"]["lng"]

    st.rerun()


# =========================================================
# FOOTER
# =========================================================

st.markdown("---")

st.markdown(
    """
**SpriteScope**  
Conçu par **Sylvain Reybaut** © 2026 — Tous droits réservés.

Cette application est une aide visuelle à la chasse aux sprites.  
Les calculs restent théoriques et l’apparition des sprites ne peut jamais être garantie.

Pour en savoir plus sur les red sprites :  
http://www.reybaut.fr

Follow me on Instagram :  
https://www.instagram.com/sylvain.reybaut/
"""
)
