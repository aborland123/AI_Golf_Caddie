import streamlit as st
import pandas as pd
import json
from datetime import datetime, timedelta
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
sheet = client.open_by_key("1u2UvRf98JBITQOFPXOKXhzK70r1bQPewLzeuvkU8CwQ").sheet1
swing_sheet = client.open_by_key("1yZTaRmJxKgcwNoo87ojVaHNbcHuSIIHT8OcBXwCsYCg").sheet1

# Sidebar navigation buttons
st.sidebar.markdown("## 📁 Menu")
home_btn = st.sidebar.button("🏠 Home", use_container_width=True)
add_entry_btn = st.sidebar.button("➕ Add Data Entry", use_container_width=True)
log_swing_btn = st.sidebar.button("📝 Log Swing", use_container_width=True)

if home_btn:
    st.session_state["page"] = "home"
elif add_entry_btn:
    st.session_state["page"] = "add"
elif log_swing_btn:
    st.session_state["page"] = "swing"

if "page" not in st.session_state:
    st.session_state["page"] = "home"

# ---------------- HOME PAGE ---------------- #
if st.session_state["page"] == "home":
    st.title("🏌️‍♂️ AI Golf Caddie Tracker")
    st.markdown("Hi Alli and friends.")

# ---------------- ADD ENTRY PAGE ---------------- #
elif st.session_state["page"] == "add":
    st.title("➕ Add New Data Entry")

    with st.form("practice_form", clear_on_submit=True):
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
            st.info("🎉 That was submitted.")
        else:
            st.error("⚠️ Please fill out all required fields before saving.")

# ---------------- SWING LOGGER PAGE ---------------- #
elif st.session_state["page"] == "swing":
    st.title("📝 Swing Direction Logger")
    st.markdown("Log the direction of each individual swing quickly and efficiently.")

    with st.expander("📋 Session Setup", expanded=True):
        location = st.text_input("Practice Location (e.g., TopGolf)", key="swing_location")
        session_duration = st.number_input("Estimated Session Duration (in hours)", min_value=1, max_value=10, value=3, key="swing_duration")
        base_date = datetime.today()
        session_id = f"{location.lower().replace(' ', '')}{base_date.strftime('%m%d')}"
        st.text(f"📎 Generated Session ID: {session_id}")

        if "session_start" not in st.session_state:
            st.session_state.session_start = datetime.now()
            st.session_state.session_end = st.session_state.session_start + timedelta(hours=session_duration)
            st.session_state.session_id = session_id
            st.session_state.swing_count = 1
            st.session_state.timer_started = True

    now = datetime.now()
    session_active = now <= st.session_state.session_end
    if session_active:
        time_left = st.session_state.session_end - now
        st.info(f"⏳ Session active. Time remaining: {str(time_left).split('.')[0]}")
    else:
        st.warning("🚨 Your session has ended. Please restart or set up a new session.")

    if session_active:
        st.divider()
        st.subheader("🎯 Log New Swing")
        with st.form("swing_logger", clear_on_submit=True):
            club = st.selectbox("Club Used", ["", "Driver", "3 Wood", "5 Iron", "7 Iron", "9 Iron", "Pitching Wedge", "Putter"], key="club")
            direction = st.radio("Direction", ["Straight", "Left", "Right"], horizontal=True, key="direction")
            timestamp = datetime.now().strftime("%H:%M:%S")
            submit_swing = st.form_submit_button("Save Swing")

        if submit_swing:
            if club:
                new_row = pd.DataFrame({
                    "Session ID": [st.session_state.session_id],
                    "Shot #": [st.session_state.swing_count],
                    "Date": [base_date.strftime("%Y-%m-%d")],
                    "Time": [timestamp],
                    "Club": [club],
                    "Direction": [direction]
                })

                existing_data = pd.DataFrame(swing_sheet.get_all_records())
                updated_data = pd.concat([existing_data, new_row], ignore_index=True)
                set_with_dataframe(swing_sheet, updated_data)

                st.success(f"✅ Shot #{st.session_state.swing_count} saved at {timestamp} with {club} going {direction}.")
                st.info("🎉 That was submitted.")
                st.session_state.swing_count += 1
            else:
                st.error("Please select a club before saving.")

        existing_data = pd.DataFrame(swing_sheet.get_all_records())
        if not existing_data.empty:
            st.divider()
            st.subheader("📈 Latest Swings")
            recent = existing_data[existing_data["Session ID"] == st.session_state.session_id].tail(10)
            st.dataframe(recent, use_container_width=True)