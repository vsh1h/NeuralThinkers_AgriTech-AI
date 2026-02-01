import streamlit as st
import sqlite3
import hashlib
from streamlit_js_eval import get_geolocation


def connect_db():
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


@st.dialog("📍 Location Permission Request")
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

    location = get_geolocation()

    if location:
       
        if 'coords' in location:
            lat = location['coords'].get('latitude')
            lon = location['coords'].get('longitude')
        else:
            lat = location.get('latitude')
            lon = location.get('longitude')

        if lat is not None and lon is not None:
            st.success(f" Location identified: {lat}, {lon}")
        else:
            st.warning("Location detected, but coordinates are unavailable.")

        st.divider()
        st.subheader("Field & Crop Information")

        with st.form("farmer_data_form"):
            col1, col2 = st.columns(2)

            with col1:
                soil_type = st.selectbox(
                    "Select Soil Type",
                    ["Clay", "Silt", "Sandy", "Black Soil", "Loamy","Red soil"]
                )
                crop_type = st.selectbox(
                    "Crop Type",
                    ["Rice", "Wheat", "Cotton", "Sugarcane", "Maize"]
                )

            with col2:
                ph_level = st.number_input(
                    "Soil pH Level",
                    min_value=0.0,
                    max_value=14.0,
                    value=7.0,
                    step=0.1
                )
                st.caption("Standard pH for most crops is 6.0 - 7.5")

            fert_used = st.toggle("Did you use fertilizer?")
            if fert_used:
                f_amount = st.number_input("Amount (ml per unit)", min_value=0.0)

            submitted = st.form_submit_button("Get AI Recommendations")

            if submitted:
                st.info("AI Agent is analyzing your field context...")

    else:
        st.warning(
            "Waiting for location permission... "
            "Please check your browser's address bar."
        )

    if st.sidebar.button("Logout"):
        st.session_state.authenticated = False
        st.session_state.page = "login"
        st.session_state.location_allowed = False
        st.rerun()


def main():
    connect_db()

    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'page' not in st.session_state:
        st.session_state.page = "login"

    if st.session_state.authenticated:
        welcome_page()
    else:
        if st.session_state.page == "login":
            login_page()
        elif st.session_state.page == "register":
            register_page()


if __name__ == "__main__":
    main()
