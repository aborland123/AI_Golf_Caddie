import streamlit as st
import pandas as pd
import json
from datetime import datetime
import pytz
import gspread
from google.oauth2 import service_account
from gspread_dataframe import set_with_dataframe

# -------------------- CONFIG & AUTH --------------------
st.set_page_config(page_title="AI Golf Caddie Tracker 🏌🏻‍♀️", layout="centered")

scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
gcp_info = dict(st.secrets["gcp_service_account"])
creds = service_account.Credentials.from_service_account_info(gcp_info, scopes=scope)
client = gspread.authorize(creds)

# Sheets
sheet = client.open_by_key("1u2UvRf98JBITQOFPXOKXhzK70r1bQPewLzeuvkU8CwQ").sheet1  # Session data
swing_sheet = client.open_by_key("1yZTaRmJxKgcwNoo87ojVaHNbcHuSIIHT8OcBXwCsYCg").sheet1  # Swings

# -------------------- NAVIGATION --------------------
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

# -------------------- SWING LOGGER --------------------
elif st.session_state["page"] == "swing":
    st.title("📝 Swing Direction Logger")

    with st.expander("📋 Start New Session"):
        location_input = st.text_input("Practice Location (e.g. TopGolf)", key="swing_location")
        if st.button("🔄 Start New Session"):
            eastern = pytz.timezone("US/Eastern")
            now = datetime.now(eastern)
            today_str = now.strftime("%Y-%m-%d")
            session_id = f"{location_input.lower().replace(' ', '')}{now.strftime('%m%d')}"

            # Get existing swings
            all_swings = pd.DataFrame(swing_sheet.get_all_records())

            # Filter to today + location
            recent_session = all_swings[
                (all_swings["Date"] == today_str) &
                (all_swings["Location"].str.lower() == location_input.lower())
            ]

            # If continuing session, get last shot #
            if not recent_session.empty:
                last_shot_number = recent_session["Shot #"].max()
                swing_start = last_shot_number + 1
            else:
                swing_start = 1

            # Store session state
            st.session_state.session_id = session_id
            st.session_state.swing_count = swing_start
            st.session_state.last_club = ""
            st.session_state.last_direction = "Straight"
            st.session_state.location = location_input
            st.success(f"✅ New session started: {session_id} | Starting at shot #{swing_start}")

    if "session_id" not in st.session_state:
        st.info("👆 Start a new session to begin logging swings.")
    else:
        st.subheader("🎯 Log New Swing")

        # Maintain last-used club and direction
        club_list = ["", "Driver", "3 Wood", "5 Iron", "7 Iron", "9 Iron", "Pitching Wedge", "Putter"]
        default_club = st.session_state.get("last_club", "")
        default_dir = st.session_state.get("last_direction", "Straight")

        club_index = club_list.index(default_club) if default_club in club_list else 0
        direction_index = ["Straight", "Left", "Right"].index(default_dir)

        with st.form("swing_logger", clear_on_submit=True):
            club = st.selectbox("Club Used", club_list, index=club_index)
            direction = st.radio("Direction", ["Straight", "Left", "Right"], horizontal=True, index=direction_index)
            comment = st.text_input("Notes (optional)")
            submit_swing = st.form_submit_button("Save Swing")

        if submit_swing:
            if club:
                eastern = pytz.timezone("US/Eastern")
                now = datetime.now(eastern)

                # Save current selection after submit
                st.session_state.last_club = club
                st.session_state.last_direction = direction

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

                # Append to Google Sheet
                existing_data = pd.DataFrame(swing_sheet.get_all_records())
                updated_data = pd.concat([existing_data, new_row], ignore_index=True)
                set_with_dataframe(swing_sheet, updated_data)

                st.success(f"✅ Shot #{st.session_state.swing_count} saved.")
                st.info("🎉 That was submitted.")
                st.session_state.swing_count += 1
            else:
                st.error("⚠️ Please select a club.")

        # Show latest swings
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