import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import gspread
from google.oauth2 import service_account
from gspread_dataframe import set_with_dataframe

# Setup
st.set_page_config(page_title="AI Golf Caddie Tracker 🏌️‍♀️", layout="centered")

scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
gcp_info = dict(st.secrets["gcp_service_account"])
creds = service_account.Credentials.from_service_account_info(gcp_info, scopes=scope)
client = gspread.authorize(creds)

# Google Sheets
sheet = client.open_by_key("1u2UvRf98JBITQOFPXOKXhzK70r1bQPewLzeuvkU8CwQ").sheet1
swing_sheet = client.open_by_key("1yZTaRmJxKgcwNoo87ojVaHNbcHuSIIHT8OcBXwCsYCg").sheet1

# Sidebar navigation
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

# -------------------- HOME --------------------
if st.session_state["page"] == "home":
    st.title("🏌️‍♂️ AI Golf Caddie Tracker")
    st.markdown("Welcome back, Alli 👋")

# -------------------- ADD DATA ENTRY PAGE --------------------
elif st.session_state["page"] == "add":
    st.title("➕ Add New Data Entry")

    with st.form("practice_form", clear_on_submit=True):
        practice_type = st.selectbox("Practice Type", ["", "Driving Range", "9-Hole Course", "18-Hole Course"])
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
            eastern = pytz.timezone("US/Eastern")
            now = datetime.now(eastern)
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

            existing_data = pd.DataFrame(sheet.get_all_records())
            updated_data = pd.concat([existing_data, new_data], ignore_index=True)
            set_with_dataframe(sheet, updated_data)

            st.success("✅ Entry saved to Google Sheets!")
            st.info("🎉 That was submitted.")
        else:
            st.error("⚠️ Please fill out all required fields before saving.")

elif st.session_state["page"] == "swing":
    st.title("📝 Swing Direction Logger")

    with st.expander("📋 Start New Session"):
        location_input = st.text_input("Practice Location (e.g. TopGolf)", key="swing_location")
        if st.button("🔄 Start New Session"):
            eastern = pytz.timezone("US/Eastern")
            now = datetime.now(eastern)
            today_str = now.strftime("%Y-%m-%d")
            session_id = f"{location_input.lower().replace(' ', '')}{now.strftime('%m%d')}"

            all_swings = pd.DataFrame(swing_sheet.get_all_records())
            recent_session = all_swings[
                (all_swings["Date"] == today_str) &
                (all_swings["Location"].str.lower() == location_input.lower())
            ]

            swing_start = recent_session["Shot #"].max() + 1 if not recent_session.empty else 1

            st.session_state.session_id = session_id
            st.session_state.swing_count = swing_start
            st.session_state.last_club = ""
            st.session_state.last_direction = "Straight"
            st.session_state.location = location_input
            st.success(f"✅ New session started: {session_id} | Shot #{swing_start}")

    if "session_id" not in st.session_state:
        st.info("👆 Start a new session to begin logging swings.")
    else:
        st.subheader("🎯 Log New Swing")

        club_list = ["", "Driver", "3 Wood", "5 Iron", "7 Iron", "9 Iron", "Pitching Wedge", "Putter"]
        default_club = st.session_state.get("last_club", "")
        default_dir = st.session_state.get("last_direction", "Straight")

        club_index = club_list.index(default_club) if default_club in club_list else 0

        with st.form("swing_logger", clear_on_submit=True):
            club = st.selectbox("Club Used", club_list, index=club_index)
            direction = st.radio(
                "Direction",
                ["Straight", "Left", "Right"],
                horizontal=True,
                key="selected_direction"
            )
            comment = st.text_input("Notes (optional)")
            submit_swing = st.form_submit_button("Save Swing")

        if submit_swing:
            if club:
                st.session_state.last_club = club
                st.session_state.last_direction = st.session_state.selected_direction
                eastern = pytz.timezone("US/Eastern")
                now = datetime.now(eastern)

                new_row = pd.DataFrame({
                    "Session ID": [st.session_state.session_id],
                    "Shot #": [st.session_state.swing_count],
                    "Date": [now.strftime("%Y-%m-%d")],
                    "Time": [now.strftime("%H:%M:%S")],
                    "Location": [st.session_state.location],
                    "Club": [club],
                    "Direction": [direction],
                    "Notes": [comment]
                })

                existing_data = pd.DataFrame(swing_sheet.get_all_records())
                updated_data = pd.concat([existing_data, new_row], ignore_index=True)
                set_with_dataframe(swing_sheet, updated_data)

                st.success(f"✅ Shot #{st.session_state.swing_count} saved.")
                st.info("🎉 That was submitted.")
                st.session_state.swing_count += 1
            else:
                st.error("⚠️ Please select a club.")

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