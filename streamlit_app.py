import streamlit as st
import pandas as pd
import os
from datetime import datetime

## titles
st.set_page_config(page_title="AI Golf Caddie Tracker", layout="centered")
menu = st.sidebar.selectbox("Sidebar", ["Home 🏠", "Add Golf Data 🏌🏻‍♀️"])

file_path = "golf_data.csv"

if menu == "Home 🏠":
    st.title("🏌️‍♂️ AI Golf Caddie Tracker")

elif menu == "Add Golf Data 🏌🏻‍♀️":
    st.title("Add Golf Data 🏌🏻‍♀️")

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

    # Validate required fields
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

            if not os.path.exists(file_path):
                new_data.to_csv(file_path, index=False)
            else:
                new_data.to_csv(file_path, mode="a", header=False, index=False)

            st.success("✅ Entry saved to golf_data.csv!")
        else:
            st.error("⚠️ Please fill out all required fields before saving.")