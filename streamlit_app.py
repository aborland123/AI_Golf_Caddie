import streamlit as st
import pandas as pd
import json
from datetime import datetime
import gspread
from google.oauth2 import service_account
from gspread_dataframe import set_with_dataframe

# Set up Streamlit page
st.set_page_config(page_title="AI Golf Caddie Tracker 🏌🏻‍♀️", layout="centered")

# Set up Google Sheets connection via Streamlit Secrets
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
gcp_info = dict(st.secrets["gcp_service_account"])
creds = service_account.Credentials.from_service_account_info(gcp_info, scopes=scope)
client = gspread.authorize(creds)
sheet = client.open("golf_data_log").sheet1 

# Sidebar navigation buttons
st.sidebar.markdown("## 📁 Menu")
home_btn = st.sidebar.button("🏠 Home", use_container_width=True)
add_entry_btn = st.sidebar.button("➕ Add Data Entry", use_container_width=True)

if home_btn:
    st.session_state["page"] = "home"
elif add_entry_btn:
    st.session_state["page"] = "add"

if "page" not in st.session_state:
    st.session_state["page"] = "home"

# ---------------- HOME PAGE ---------------- #
if st.session_state["page"] == "home":
    st.title("🏌️‍♂️ AI Golf Caddie Tracker")
    st.markdown("Welcome! Use the sidebar to add a new golf practice session.")

# ---------------- ADD ENTRY PAGE ---------------- #
elif st.session_state["page"] == "add":
    st.title("➕ Add New Data Entry")

    with st.form("practice_form"):
        practice_type = st.selectbox("Practice Type", [
            "", "Driving Range", "9-Hole Course", "18-Hole Course"
        ])
        date = st.date_input("Date", value=datetime.today())
        start_time = st.time_input("Start Time")
        end_time = st.time_input("End Time")
        location = st.text_input("Location (e.g. TopGolf Charlotte)")
        ball_used = st.text_input("Ball Used (optional)")
        comments = st.text_area("Comments (optional)")

        st.markdown("---")
        st.subheader("🌤️ Weather & Environment")

        avg_temp = st.number_input("Average Temperature (°F)", min_value=30, max_value=120)
        feels_like = st.number_input("Feels Like Temperature (°F)", min_value=30, max_value=120)
        uv_index = st.number_input("UV Index", min_value=0.0, max_value=11.0, step=0.1)
        wind_speed = st.number_input("Wind Speed (MPH)", min_value=0.0, step=0.5)
        wind_gusts = st.number_input("Wind Gusts (MPH)", min_value=0.0, step=0.5)
        wind_dir = st.text_input("Wind Direction (e.g. N, NW, SE)")
        humidity = st.number_input("Humidity (%)", min_value=0, max_value=100)
        aqi = st.number_input("Air Quality Index (AQI)", min_value=0, max_value=500)

        submitted = st.form_submit_button("Save Entry")

    required_fields = [practice_type, location, wind_dir]
    if submitted:
        if all(required_fields):
            new_data = pd.DataFrame({
                "Date": [date],
                "Start Time": [start_time.strftime("%H:%M")],
                "End Time": [end_time.strftime("%H:%M")],
                "Practice Type": [practice_type],
                "Location": [location],
                "Ball Used": [ball_used],
                "Avg Temp (°F)": [avg_temp],
                "Feels Like (°F)": [feels_like],
                "UV Index": [uv_index],
                "Wind Speed (MPH)": [wind_speed],
                "Wind Gusts (MPH)": [wind_gusts],
                "Wind Direction": [wind_dir],
                "Humidity (%)": [humidity],
                "AQI": [aqi],
                "Comments": [comments]
            })

            existing_data = pd.DataFrame(sheet.get_all_records())
            updated_data = pd.concat([existing_data, new_data], ignore_index=True)
            set_with_dataframe(sheet, updated_data)

            st.success("✅ Entry saved to Google Sheets!")
        else:
            st.error("⚠️ Please fill out all required fields before saving.")