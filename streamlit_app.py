import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import gspread
from google.oauth2 import service_account
from gspread_dataframe import set_with_dataframe

# --- PAGE CONFIG ---
st.set_page_config(page_title="AI Golf Caddie Tracker 🏌️‍♀️", layout="centered")

# --- AUTH & GOOGLE SHEETS ---
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
gcp_info = dict(st.secrets["gcp_service_account"])
creds = service_account.Credentials.from_service_account_info(gcp_info, scopes=scope)
client = gspread.authorize(creds)

# Sheets
session_sheet = client.open_by_key("1u2UvRf98JBITQOFPXOKXhzK70r1bQPewLzeuvkU8CwQ").sheet1  # golf_data_log
swing_sheet = client.open_by_key("1yZTaRmJxKgcwNoo87ojVaHNbcHuSIIHT8OcBXwCsYCg").sheet1  # golf_shot_data_log

# Eastern Time
eastern = pytz.timezone("US/Eastern")
now = datetime.now(eastern)

# --- SIDEBAR ---
st.sidebar.markdown("## 📁 Menu")
home_btn = st.sidebar.button("Home 🏠", use_container_width=True)
add_entry_btn = st.sidebar.button("Add Data Entry ➕", use_container_width=True)
log_swing_btn = st.sidebar.button("Swing Logger 📝", use_container_width=True)

if home_btn:
    st.session_state["page"] = "home"
elif add_entry_btn:
    st.session_state["page"] = "add"
elif log_swing_btn:
    st.session_state["page"] = "swing"
if "page" not in st.session_state:
    st.session_state["page"] = "home"

# --- HOME PAGE ---
if st.session_state["page"] == "home":
    st.title("AI Golf Caddie Tracker 🏌️‍♀️")
    st.markdown("Welcome back, Alli! Use the menu to log swings or session data. ⛳")

# --- ADD DATA ENTRY TAB ---
elif st.session_state["page"] == "add":
    st.title("Add New Data Entry ➕")

    with st.form("practice_form", clear_on_submit=True):
        practice_type = st.selectbox("Practice Type", ["", "Driving Range", "9 Holes", "18 Holes"])
        location = st.text_input("Location (e.g. TopGolf Charlotte)")
        ball_used = st.text_input("Ball Used (optional)")
        comments = st.text_area("Comments (optional)")

        st.markdown("---")
        st.subheader("Weather & Environment 🌤️")
        avg_temp = st.number_input("Average Temperature (°F)", min_value=30, max_value=120)
        feels_like = st.number_input("Feels Like Temperature (°F)", min_value=30, max_value=120)
        uv_index = st.number_input("UV Index", min_value=0.0, max_value=11.0, step=0.1)
        wind_speed = st.number_input("Wind Speed (MPH)", min_value=0.0, step=0.5)
        wind_gusts = st.number_input("Wind Gusts (MPH)", min_value=0.0, step=0.5)
        wind_dir = st.text_input("Wind Direction (e.g. N, NW, SE)")
        humidity = st.number_input("Humidity (%)", min_value=0, max_value=100)
        aqi = st.number_input("Air Quality Index (AQI)", min_value=0, max_value=500)

        submitted = st.form_submit_button("Save Entry")

    if submitted:
        required_fields = [practice_type, location, wind_dir]
        if all(required_fields):
            new_data = pd.DataFrame({
                "Date": [now.strftime("%Y-%m-%d")],
                "Start Time": [now.strftime("%H:%M")],
                "End Time": [now.strftime("%H:%M")],
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

            existing_data = pd.DataFrame(session_sheet.get_all_records())
            updated_data = pd.concat([existing_data, new_data], ignore_index=True)
            set_with_dataframe(session_sheet, updated_data)

            st.success("✅ Entry saved to Google Sheets!")
        else:
            st.error("⚠️ Please fill out all required fields.")

# --- SWING LOGGER TAB ---
elif st.session_state["page"] == "swing":
    st.title("Swing Direction Logger 📝")

    with st.expander("📋 Start New Session"):
        location_input = st.text_input("Practice Location (e.g. TopGolf)")
        practice_type = st.selectbox("Practice Type", ["Driving Range", "9 Holes", "18 Holes"])
        if st.button("🔄 Start Session"):
            session_id = f"{location_input.lower().replace(' ', '')}{now.strftime('%m%d')}"
            st.session_state.session_id = session_id
            st.session_state.swing_count = 1
            st.session_state.practice_type = practice_type
            st.session_state.location = location_input
            st.success(f"✅ Session started: {session_id} | Practice: {practice_type}")

    if "session_id" in st.session_state:
        st.subheader("Log New Swing 🎯")

        # Shared fields
        club = st.selectbox("Club Used", ["", "Driver", "3 Wood", "5 Iron", "7 Iron", "9 Iron", "Pitching Wedge", "Putter"])
        direction = st.radio("Direction", ["Straight", "Left", "Right"], horizontal=True)
        feel = st.radio("How did it feel?", ["Bad", "Okay", "Good"], horizontal=True)
        notes = st.text_input("Notes (optional)")

        # Practice-specific extras
        yardage = hole_number = shot_on_hole = par = tee_color = None

        if st.session_state.practice_type == "Driving Range":
            yardage = st.number_input("Estimated Yardage (Optional)", min_value=0, step=1)

        elif st.session_state.practice_type in ["9 Holes", "18 Holes"]:
            hole_number = st.number_input("Hole Number", min_value=1, max_value=18, step=1)
            shot_on_hole = st.number_input("Shot # on This Hole", min_value=1, step=1)
            yardage = st.number_input("Yardage of Hole", min_value=0, step=1)
            par = st.selectbox("Par", [3, 4, 5])
            tee_color = st.selectbox("Tee Color", ["Red", "White", "Blue", "Gold", "Other"])

        if st.button("✅ Save Swing"):
            new_row = pd.DataFrame({
                "Session ID": [st.session_state.session_id],
                "Practice Type": [st.session_state.practice_type],
                "Date": [now.strftime("%Y-%m-%d")],
                "Time": [now.strftime("%H:%M:%S")],
                "Location": [st.session_state.location],
                "Club": [club],
                "Shot # on Hole": [shot_on_hole],
                "Direction": [direction],
                "Feel": [feel],
                "Notes": [notes],
                "Hole #": [hole_number],
                "Hole Yardage": [yardage],
                "Par": [par],
                "Tee Color": [tee_color]
            })

            existing_data = pd.DataFrame(swing_sheet.get_all_records())
            updated_data = pd.concat([existing_data, new_row], ignore_index=True)
            set_with_dataframe(swing_sheet, updated_data)

            st.success("✅ Swing saved!")
            st.session_state.swing_count += 1

        # Recent swings + summary
        all_data = pd.DataFrame(swing_sheet.get_all_records())
        if not all_data.empty:
            st.divider()
            st.subheader("📈 Latest Swings")
            recent = all_data[all_data["Session ID"] == st.session_state.session_id].tail(10)
            st.dataframe(recent, use_container_width=True)

            st.divider()
            st.subheader("📊 Shot Direction Summary")
            direction_counts = recent["Direction"].value_counts(normalize=True).mul(100).round(1).to_frame(name="%")
            st.bar_chart(direction_counts)
    else:
        st.info("Start a session above to begin logging swings.")
