__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import streamlit as st
import hashlib
from streamlit_js_eval import get_geolocation
try:
    import langchain_google_genai
    import langgraph
    import plotly
except ImportError as e:
    import streamlit as st
    import sys
    import os
    st.error(f"### Environment Error: Missing Dependencies")
    st.write(f"The module **'{e.name}'** was not found.")
    
    st.info("### Technical Diagnostics:")
    st.write(f"- **Current Python:** `{sys.executable}`")
    st.write(f"- **Working Directory:** `{os.getcwd()}`")
    
    st.warning("You are currently running the app using the **system/Anaconda Python**, which does not have the AgriTech AI libraries installed.")
    st.success("### How to fix this:")
    st.write("Run the following command in your terminal to use the correct local environment:")
    st.code("./run_app.sh")
    st.stop()

from farmer_dashboard import show_farmer_dashboard
from dotenv import load_dotenv

load_dotenv(override=True)

st.set_page_config(page_title="AgriTech AI ~ Farmer Dashboard", layout="wide")

if not st.session_state.get('authenticated', False):
    st.markdown("""
        <style>
            [data-testid="stSidebar"] {
                display: none;
            }
        </style>
    """, unsafe_allow_html=True)

def connect_db():
    if st.session_state.get('authenticated'):
        with st.sidebar.expander("System Health", expanded=False):
            st.write(f"**GPS:** {'GPS not enabled' if st.session_state.get('env_data', {}).get('location') else 'GPS enabled'}")
            
            import os
            keys = {
                "OpenWeather": bool(os.environ.get("OPENWEATHER_API_KEY")),
                "Ambee": bool(os.environ.get("AMBEE_API_KEY")),
                "OpenAI": bool(os.environ.get("OPENAI_API_KEY"))
            }
            for k, v in keys.items():
                st.write(f"**{k}:** {'configured' if v else 'not configured'}")
                
            if st.session_state.get('env_data'):
                st.json(st.session_state.env_data['location'])

    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users(username TEXT, password TEXT)''')
    conn.commit()
    conn.close()

def register_user(username, password):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
    conn.commit()
    conn.close()

def authenticate(username, password):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    c.execute(
        "SELECT * FROM users WHERE username = ? AND password = ?",
        (username, hashed_password)
    )
    user = c.fetchone()
    conn.close()
    return True if user else False

def register_page():
    st.title("Create Account")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    confirm_password = st.text_input("Confirm Password", type="password")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Register"):
            if username and password and password == confirm_password:
                register_user(username, password)
                st.success("Registered successfully! Please login.")
                st.session_state.page = "login"
                st.rerun()
            elif password != confirm_password:
                st.error("Passwords do not match.")
            else:
                st.error("Please fill in all fields.")

    with col2:
        if st.button("Back to Login"):
            st.session_state.page = "login"
            st.rerun()

def login_page():
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login", type="primary"):
        if authenticate(username, password):
            st.session_state.authenticated = True
            st.session_state.page = "welcome"
            st.rerun()
        else:
            st.error("Invalid username or password")

    st.write("---")
    st.write("Don't have an account?")
    if st.button("Go to Register"):
        st.session_state.page = "register"
        st.rerun()

@st.dialog("Location Permission Request")
def location_alert():
    st.write(
        "To provide accurate weather, soil analytics, and crop suggestions, "
        "we need your location permission."
    )
    if st.button("I understand, let's proceed"):
        st.session_state.location_allowed = True
        st.rerun()

def welcome_page():
    if 'location_allowed' not in st.session_state:
        st.session_state.location_allowed = False

    st.title("Welcome to your Farm Dashboard!")

    if not st.session_state.location_allowed:
        location_alert()
        st.info("Please respond to the location permission request to proceed.")
        st.stop()

    from environment_data.wrapper import get_environmental_context
    from src.ai_logic import get_expert_analysis

    if 'env_data' not in st.session_state:
        with st.spinner("Analyzing your field environment (Weather + Soil)..."):
            env_data = get_environmental_context()
            
            if not env_data['location']:
                 st.warning("Could not detect precise location. Please ensure location is enabled.")
                 st.stop()
                 
            st.session_state.env_data = env_data
            
            analysis = get_expert_analysis(env_data['weather'], env_data['soil'])
            st.session_state.ai_analysis = analysis

    env_data = st.session_state.env_data
    analysis = st.session_state.get('ai_analysis', {})

    if env_data.get('location') and env_data['location'].get('latitude'):
        st.success(f"Location identified: {env_data['location']['latitude']:.4f}, {env_data['location']['longitude']:.4f}")
    else:
        st.warning(" Location identified but coordinates unavailable.")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Weather Context")
        w = env_data['weather']
        st.write(f"**Temp:** {w['temperature_c']}°C")
        st.write(f"**Humidity:** {w['humidity']}%")
        if w['weather_alert']:
            st.error(f" {w['weather_alert']}")
        else:
            st.info("No active weather alerts.")

    with col2:
        st.subheader("Soil Composition")
        s = env_data['soil']
        st.write(f"**Type:** {s['soil_type'] or 'Unknown'}")
        st.write(f"**Est. pH:** {s['soil_ph'] or 'N/A'}")
        st.write(f"**Moisture:** {s['soil_moisture'] or 'N/A'}%")

    st.divider()
    
    st.subheader("AI Recommendations")
    
    if analysis.get('soil_analysis'):
        st.caption(analysis['soil_analysis'])

    with st.form("farmer_data_form"):
        st.write("Based on your location and conditions, we recommend:")
        
        suggested_crops = analysis.get('suggested_crops', ["Rice", "Wheat", "Maize"])
        
        c1, c2 = st.columns(2)
        with c1:
            selected_crop = st.selectbox("Select Crop", suggested_crops)
        with c2:
            detected_soil = list([s['soil_type']]) if s['soil_type'] else []
            all_soils = detected_soil + ["Clay", "Silt", "Sandy", "Black Soil", "Loamy", "Red soil"]
            all_soils = list(dict.fromkeys(all_soils))
            
            selected_soil = st.selectbox("Confirm Soil Type", all_soils)

        ph_val = s['soil_ph'] if s['soil_ph'] else 7.0
        ph_level = st.number_input("Soil pH Level", value=float(ph_val), step=0.1)

        submitted = st.form_submit_button("Launch Dashboard")

        if submitted:
            st.session_state.soil_type = selected_soil
            st.session_state.crop_type = selected_crop
            st.session_state.ph_level = ph_level
            st.session_state.weather_alert = env_data['weather']['weather_alert']
            st.session_state.action_plan = analysis.get('action_plan', [])
            st.session_state.page = "dashboard"
            st.rerun()

    with st.sidebar:
        if st.button("Refresh Data"):
            if 'env_data' in st.session_state:
                del st.session_state.env_data
            if 'ai_analysis' in st.session_state:
                del st.session_state.ai_analysis
            st.rerun()

    if st.sidebar.button("Logout"):
        st.session_state.authenticated = False
        st.session_state.page = "login"
        st.session_state.location_allowed = False
        if 'env_data' in st.session_state:
            del st.session_state.env_data
        st.rerun()

def main():
    connect_db()

    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'page' not in st.session_state:
        st.session_state.page = "login"

    if st.session_state.authenticated:
        if st.session_state.page == "dashboard":
            show_farmer_dashboard()
        else:
            welcome_page()
    else:
        if st.session_state.page == "login":
            login_page()
        elif st.session_state.page == "register":
            register_page()

if __name__ == "__main__":
    main()
