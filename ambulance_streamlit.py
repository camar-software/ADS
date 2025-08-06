from datetime import datetime
import streamlit as st
import folium
from streamlit_folium import st_folium
import uuid
from geopy.geocoders import Nominatim

# Streamlit Page Config
st.set_page_config(page_title="Ambulance Dispatch Dashboard", layout="wide")

# Geocoder
geolocator = Nominatim(user_agent="ambulance_dispatch_app")

@st.cache_resource(show_spinner=False)
def get_place_name(lat, lng):
    try:
        location = geolocator.reverse((lat, lng), exactly_one=True, timeout=10)
        return location.address.split(",")[0]
    except:
        return "Unknown Location"

# CSS Styling
st.markdown("""
    <style>
    [data-testid="stSidebar"] {
        padding: 2rem 1.5rem;
    }
    .sidebar-title {
        font-size: 24px;
        font-weight: 700;
        color: black;
        margin-bottom: 2rem;
    }
    .stRadio > div {
        display: flex;
        flex-direction: column;
        gap: 28px;
    }
   
    .stRadio > div > label:hover {
        background-color: rgba(255,255,255,0.15);
        cursor: pointer;
    }
    </style>
""", unsafe_allow_html=True)

# Data Models
class Ambulance:
    def __init__(self, driver_name, plate_number, status, location):
        self.id = str(uuid.uuid4())
        self.driver_name = driver_name
        self.plate_number = plate_number
        self.status = status
        self.location = location

class Incident:
    def __init__(self, incident_type, location, severity):
        self.id = str(uuid.uuid4())
        self.incident_type = incident_type
        self.location = location
        self.severity = severity
        self.reported_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

class Dispatch:
    def __init__(self, ambulance_plate, incident_id):
        self.id = str(uuid.uuid4())
        self.plate_number = ambulance_plate
        self.incident_id = incident_id
        self.time_dispatched = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.status = "Dispatched"

# Session State
if "ambulances" not in st.session_state:
    st.session_state.ambulances = []

if "incidents" not in st.session_state:
    st.session_state.incidents = []

if "dispatches" not in st.session_state:
    st.session_state.dispatches = []

# Sidebar Navigation
page_map = {
    "Register Ambulance": "➕ Register Ambulance",
    "Report Incident": "📍 Report Incident",
    "List Ambulances": "🚑 View Ambulances",
    "List Incidents": "📌 View Incidents",
    "Dispatch Ambulance": "🚨 Dispatch Emergency",
    "Map View": "🗺️ Live Map"
}

# Styled Sidebar with spacing
st.sidebar.markdown('<div class="sidebar-title">🚑 Dispatch System</div>', unsafe_allow_html=True)
page = st.sidebar.radio("Select", list(page_map.keys()), format_func=lambda x: page_map[x])
st.sidebar.markdown("<br><br><hr style='border-color: blue;'>", unsafe_allow_html=True)

# Utility: Map Click Picker
def map_picker(prompt="Click on the map to choose location"):
    st.markdown(f"### {prompt}")
    map_center = [1.2921, 36.8219]
    m = folium.Map(location=map_center, zoom_start=10)
    map_result = st_folium(m, height=400, width=700, returned_objects=["last_clicked"])
    coords = map_result.get("last_clicked")
    return coords

# Register Ambulance Page
if page == "Register Ambulance":
    st.title("➕ Register New Ambulance")
    with st.form("register_form"):
        col1, col2 = st.columns(2)
        with col1:
            driver_name = st.text_input("Driver Name")
            plate_number = st.text_input("Plate Number")
            status = st.selectbox("Status", ["Available", "Busy"])
        with col2:
            coords = map_picker("Choose Ambulance Location")
        submitted = st.form_submit_button("Register Ambulance")

        if submitted and coords:
            amb = Ambulance(driver_name, plate_number, status, coords)
            st.session_state.ambulances.append(amb)
            st.success(f"✅ Ambulance {plate_number} registered.")
        elif submitted:
            st.error("⚠️ Please select a location on the map.")

# Report Incident Page
elif page == "Report Incident":
    st.title("📍 Report New Incident")
    with st.form("incident_form"):
        col1, col2 = st.columns(2)
        with col1:
            incident_type = st.selectbox("Incident Type", ["Accident", "Medical", "Fire", "Other"])
            severity = st.selectbox("Severity", ["Low", "Medium", "High"])
        with col2:
            coords = map_picker("Choose Incident Location")
        submitted = st.form_submit_button("Report Incident")

        if submitted and coords:
            incident = Incident(incident_type, coords, severity)
            st.session_state.incidents.append(incident)
            st.success("✅ Incident reported.")
        elif submitted:
            st.error("⚠️ Please select a location on the map.")

# List Ambulances Page
elif page == "List Ambulances":
    st.title("🚑 Registered Ambulances")
    if not st.session_state.ambulances:
        st.warning("No ambulances registered yet.")
    else:
        for amb in st.session_state.ambulances:
            place = get_place_name(amb.location["lat"], amb.location["lng"])
            st.markdown(f"""
            **Driver:** {amb.driver_name}  
            **Plate:** `{amb.plate_number}`  
            **Status:** {amb.status}  
            **Location:** {place}  
            ---
            """)

# List Incidents Page
elif page == "List Incidents":
    st.title("📌 Reported Incidents")
    if not st.session_state.incidents:
        st.info("No incidents reported yet.")
    else:
        for inc in st.session_state.incidents:
            place = get_place_name(inc.location["lat"], inc.location["lng"])
            st.markdown(f"""
            **Type:** {inc.incident_type}  
            **Severity:** {inc.severity}  
            **Reported At:** {inc.reported_time}  
            **Location:** {place}  
            ---
            """)

# Dispatch Ambulance Page
elif page == "Dispatch Ambulance":
    st.title("🚨 Dispatch Ambulance")
    available = [a for a in st.session_state.ambulances if a.status == "Available"]
    if not available:
        st.warning("No available ambulances.")
    elif not st.session_state.incidents:
        st.warning("No incidents to dispatch.")
    else:
        amb_selected = st.selectbox("Select Ambulance", [a.plate_number for a in available])
        inc_selected = st.selectbox("Select Incident", [
            f"{i.incident_type} | {i.severity} | {i.reported_time}" for i in st.session_state.incidents
        ])
        if st.button("Dispatch Now"):
            amb = next((a for a in available if a.plate_number == amb_selected), None)
            amb.status = "Busy"
            inc = next(i for i in st.session_state.incidents if f"{i.incident_type} | {i.severity} | {i.reported_time}" == inc_selected)
            dispatch = Dispatch(amb.plate_number, inc.id)
            st.session_state.dispatches.append(dispatch)
            st.success(f"🚑 Ambulance {amb.plate_number} dispatched at {dispatch.time_dispatched}.")

# Map View Page
elif page == "Map View":
    st.title("🗺️ Emergency Map View")
    m = folium.Map(location=[1.2921, 36.8219], zoom_start=12)

    for amb in st.session_state.ambulances:
        place = get_place_name(amb.location["lat"], amb.location["lng"])
        folium.Marker(
            location=[amb.location["lat"], amb.location["lng"]],
            popup=f"Ambulance: {amb.driver_name} | Plate: {amb.plate_number} | {amb.status} | {place}",
            icon=folium.Icon(color="green" if amb.status == "Available" else "orange", icon="ambulance")
        ).add_to(m)

    for inc in st.session_state.incidents:
        place = get_place_name(inc.location["lat"], inc.location["lng"])
        folium.Marker(
            location=[inc.location["lat"], inc.location["lng"]],
            popup=f"Incident: {inc.incident_type} | {inc.severity} | {inc.reported_time} | {place}",
            icon=folium.Icon(color="red", icon="info-sign")
        ).add_to(m)

    st_data = st_folium(m, height=500, width=900)

# Dispatch Log (Optional)
if st.session_state.dispatches:
    with st.expander("📜 Dispatch Log", expanded=False):
        for d in st.session_state.dispatches:
            st.write(f"🕒 {d.time_dispatched} | 🚑 {d.plate_number} | ✅ {d.status}")
