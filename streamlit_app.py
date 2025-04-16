import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import gspread
from google.oauth2 import service_account
from gspread_dataframe import set_with_dataframe

# ---------------- SETUP ---------------- #
st.set_page_config(page_title="AI Golf Caddie Tracker 🏌️‍♀️", layout="centered")

# Google Auth + Sheets
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
gcp_info = dict(st.secrets["gcp_service_account"])
creds = service_account.Credentials.from_service_account_info(gcp_info, scopes=scope)
client = gspread.authorize(creds)
swing_sheet = client.open_by_key("1yZTaRmJxKgcwNoo87ojVaHNbcHuSIIHT8OcBXwCsYCg").sheet1  # golf_shot_data_log

# Timezone
eastern = pytz.timezone("US/Eastern")
now = datetime.now(eastern)

# ---------------- SIDEBAR NAV ---------------- #
st.sidebar.markdown("## 📁 Menu")
home_btn = st.sidebar.button("Home 🏠", use_container_width=True)
log_swing_btn = st.sidebar.button("Swing Logger 📝", use_container_width=True)

if home_btn:
    st.session_state["page"] = "home"
elif log_swing_btn:
    st.session_state["page"] = "swing"
if "page" not in st.session_state:
    st.session_state["page"] = "home"

# ---------------- HOME ---------------- #
if st.session_state["page"] == "home":
    st.title("AI Golf Caddie Tracker 🏌️‍♀️")
    st.markdown("Welcome back, Alli! Use the menu to log swings. ⛳")

# ---------------- SWING LOGGER ---------------- #
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

        # Common inputs
        club = st.selectbox("Club Used", ["", "Driver", "3 Wood", "5 Iron", "7 Iron", "9 Iron", "Pitching Wedge", "Putter"])
        direction = st.radio("Direction", ["Straight", "Left", "Right"], horizontal=True)
        feel = st.radio("How did it feel?", ["Bad", "Okay", "Good"], horizontal=True)
        notes = st.text_input("Notes (optional)")

        # Practice-type-specific fields
        yardage = None
        hole_number = None
        shot_on_hole = None
        par = None
        tee_color = None

        if st.session_state.practice_type == "Driving Range":
            yardage = st.number_input("Estimated Yardage (Optional)", min_value=0, step=1)

        elif st.session_state.practice_type in ["9 Holes", "18 Holes"]:
            hole_number = st.number_input("Hole Number", min_value=1, max_value=18, step=1)
            shot_on_hole = st.number_input("Shot # on This Hole", min_value=1, step=1)
            yardage = st.number_input("Yardage of Hole", min_value=0, step=1)
            par = st.selectbox("Par", [3, 4, 5])
            tee_color = st.selectbox("Tee Color", ["Red", "White", "Blue", "Gold", "Other"])

        # Save swing
        if st.button("✅ Save Swing"):
            new_row = pd.DataFrame({
                "Session ID": [st.session_state.session_id],
                "Practice Type": [st.session_state.practice_type],
                "Date": [now.strftime("%Y-%m-%d")],
                "Time": [now.strftime("%H:%M:%S")],
                "Location": [st.session_state.location],
                "Club": [club],
                "Direction": [direction],
                "Feel": [feel],
                "Notes": [notes],
                "Hole #": [hole_number],
                "Shot # on Hole": [shot_on_hole],
                "Hole Yardage": [yardage],
                "Par": [par],
                "Tee Color": [tee_color]
            })

            existing_data = pd.DataFrame(swing_sheet.get_all_records())
            updated_data = pd.concat([existing_data, new_row], ignore_index=True)
            set_with_dataframe(swing_sheet, updated_data)

            st.success("✅ Swing saved!")
            st.session_state.swing_count += 1

        # Show recent swings
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