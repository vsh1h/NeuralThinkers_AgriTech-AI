import streamlit as st
import sqlite3
import hashlib

def connect_db():
    conn=sqlite3.connect('users.db')
    c=conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users(username TEXT, password TEXT)''')
    conn.commit()
    conn.close()

def register_user(username,password):
    conn=sqlite3.connect('users.db')
    c=conn.cursor()
    hashed_password=hashlib.sha256(password.encode()).hexdigest()
    c.execute(
    "INSERT INTO users (username, password) VALUES (?, ?)",
    (username, hashed_password)
)

    conn.commit()
    conn.close()

def authenticate(username,password):
    conn=sqlite3.connect('users.db')
    c=conn.cursor()
    hashed_password=hashlib.sha256(password.encode()).hexdigest()
    c.execute(
    "SELECT * FROM users WHERE username = ? AND password = ?",
    (username, hashed_password)
)

    user=c.fetchone()
    conn.close()
    if user:
        return True
    else:
        return False
    
def register_page():
    st.title("Register Page")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    confirm_password = st.text_input("Confirm Password", type="password")

    if st.button("Register"):
        if username and password and password == confirm_password:
            register_user(username, password)
            st.success("Registered successfully! Please login.")
            st.session_state.page = "login"
        elif password != confirm_password:
            st.error("Passwords do not match.")
        else:
            st.error("Please enter both username and password.")


def login_page():
    st.title("Login Page")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if authenticate(username, password):
            st.session_state.authenticated = True
            st.success("Logged in successfully!")
            st.session_state.page = "welcome"
        else:
            st.error("Invalid username or password")

def welcome_page():
    st.title("Welcome Page")
    st.write("You are now logged in!")

    if "authenticated" in st.session_state and st.session_state.authenticated:
        st.write("Here is some Python content!")
        st.text("This is a Python text only visible to logged-in users.")

        if st.button("Logout"):
            st.session_state.authenticated = False
            st.session_state.page = "login"
            st.success("Logged out successfully!")


def main():
    connect_db()

    if 'authenticated' not in st.session_state:
        st.session_state.authenticated=False
        st.session_state.page="login"


    if 'authenticated' in st.session_state and st.session_state.authenticated:
        page=st.sidebar.selectbox("Select a page",["Welcome","Logout"])
        if page=="Welcome":
            st.session_state.page="welcome"

        if page=="Logout":
            st.session_state.authenticated=False
            st.session_state.page="login"
            st.success("You have logged out!")

    else: 
        page=st.sidebar.selectbox("Select a page",["Login","Register"])
        if page=="Login":
            st.session_state.page="login"
        if page=="Register":
            st.session_state.page="register"

    if st.session_state.page == "login":
        login_page()
    elif st.session_state.page == "register":
        register_page()
    elif st.session_state.page == "welcome":
        welcome_page()
 

        


if __name__=="__main__":
    main()
