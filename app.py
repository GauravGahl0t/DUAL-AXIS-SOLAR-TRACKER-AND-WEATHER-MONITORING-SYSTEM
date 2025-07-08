import streamlit as st
import pandas as pd
import numpy as np
import joblib
import plotly.express as px
import requests
from streamlit_option_menu import option_menu

st.set_page_config(page_title="Solar Tracker Dashboard", layout="wide")

# Injecting custom CSS styles
st.markdown("""
    <style>
    .rain-header {color: #1E88E5;}
    .solar-header {color: #F9A825;}
    .subsection-title {font-size: 20px; font-weight: bold; margin-top: 20px;}
    .metric-box {background-color: #e3f2fd; padding: 10px; border-radius: 10px;}
    .stButton > button {background-color: #00897B; color: white;}
    .stMarkdown h2 {margin-bottom: 0.2em;}
    </style>
""", unsafe_allow_html=True)

# Sidebar menu
with st.sidebar:
    menu = option_menu('Solar Tracker Dashboard', [
        '🌤️ Manual Prediction',
        '🔁 Automated Prediction',
        '⚡ Solar Power Output'
    ],
        default_index=0,
        styles={
            "container": {"padding": "5px", "background-color": "#F0F2F6"},
            "icon": {"color": "orange", "font-size": "18px"},
            "nav-link": {"font-size": "16px", "text-align": "left", "margin": "0px"},
            "nav-link-selected": {"background-color": "#ffd54f"},
        })

# ----------------- Loaders -------------------
def load_google_sheets():
    sheet_url = "https://docs.google.com/spreadsheets/d/1FJL6mVDp7xfxs0w2Jmnw7dbDhUQkOnQ6muOwC5dCaAE/gviz/tq?tqx=out:csv"
    return pd.read_csv(sheet_url)

def fetch_weather_data():
    api_key = "dc982666-0d8b-11f0-95f7-0242ac130003-dc9826ca-0d8b-11f0-95f7-0242ac130003"
    lat, lon = 28.6139, 77.2090  # Delhi
    url = f"https://api.stormglass.io/v2/weather/point?lat={lat}&lng={lon}&params=cloudCover,windSpeed"
    headers = {"Authorization": api_key}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        cloud_cover = data['hours'][0]['cloudCover']['noaa']
        wind_speed = data['hours'][0]['windSpeed']['noaa']
        return cloud_cover, wind_speed
    return None, None

# ----------------- Models -------------------
def s_pred(sol_input):
    model = joblib.load('solar_power_model.sav')
    df = pd.DataFrame([sol_input])
    df.rename(columns={"Temperature":"temperature","Humidity":"humidity","Pressure":"surface_pressure","Altitude":"altitude"}, inplace=True)
    df = df[['temperature', 'humidity', 'surface_pressure', 'altitude']].apply(pd.to_numeric, errors='coerce').fillna(0)
    return model.predict(df)[0]

def predict(input_data):
    model = joblib.load('xgboost_rainfall_model.sav')
    df = pd.DataFrame([input_data])
    df.rename(columns={"Wind Speed": "Wind_Speed", "Cloud Cover": "Cloud_Cover"}, inplace=True)
    df = df[['Temperature', 'Humidity', 'Wind_Speed', 'Cloud_Cover', 'Pressure']].apply(pd.to_numeric, errors='coerce').fillna(0)
    return model.predict(df)[0]

# ---------------- MENU: MANUAL ----------------
if menu == "🌤️ Manual Prediction":
    st.markdown("<h2 class='rain-header'>🌤️ Manual Rainfall Prediction</h2>", unsafe_allow_html=True)
    st.markdown("Enter the environmental conditions below:")

    user_input = {
        'Temperature': st.number_input("🌡️ Temperature (°C)", value=23.7),
        'Humidity': st.number_input("💧 Humidity (%)", value=89.6),
        'Wind Speed': st.number_input("🌬️ Wind Speed (m/s)", value=7.33),
        'Cloud Cover': st.number_input("☁️ Cloud Cover (%)", value=50.50),
        'Pressure': st.number_input("⏲️ Pressure (Pa)", value=103237.0)
    }

    if st.button("🔍 Predict Rainfall"):
        with st.spinner("Making prediction..."):
            prediction = predict(user_input)
            result = "🌧️ Predicted Rainfall: **Yes**" if prediction == 1 else "🌤️ Predicted Rainfall: **No**"
            st.success(result)

# ---------------- MENU: AUTOMATED ----------------
elif menu == "🔁 Automated Prediction":
    st.markdown("<h2 class='rain-header'>🔁 Automated Rainfall Prediction</h2>", unsafe_allow_html=True)

    if st.button("Fetch & Predict"):
        with st.spinner("Fetching data..."):
            df = load_google_sheets()
            st.dataframe(df.tail())

            if not df.empty:
                latest = df[['Temperature', 'Humidity', 'Pressure']].iloc[-1].to_dict()
                cloud_cover, wind_speed = fetch_weather_data()

                if cloud_cover is not None:
                    latest.update({"Cloud Cover": cloud_cover, "Wind Speed": wind_speed})
                    prediction = predict(latest)
                    st.success("🧠 Latest Prediction: **Rain**" if prediction == 1 else "☀️ Latest Prediction: **No Rain**")
                else:
                    st.error("Failed to fetch weather API data.")

# ---------------- MENU: SOLAR POWER OUTPUT ----------------
elif menu == "⚡ Solar Power Output":
    st.markdown("<h2 class='solar-header'>⚡ Solar Power Output Dashboard</h2>", unsafe_allow_html=True)

    df = load_google_sheets()

    if not df.empty:
        with st.spinner("Analyzing data..."):
            sol_input = df[['Temperature', 'Humidity', 'Pressure', 'Altitude']].iloc[-1].to_dict()
            predicted_power = s_pred(sol_input)

            actual_power = df["Solar Power"].iloc[-1] if "Solar Power" in df.columns else None
            threshold = 25
            anomaly_detected = False
            diff_percent = 0

            if actual_power is not None:
                difference = abs(predicted_power - actual_power)
                if predicted_power > 0:
                    diff_percent = (difference / predicted_power) * 100
                    anomaly_detected = diff_percent > threshold

            st.markdown("---")
            col1, col2 = st.columns(2)
            col1.metric("🔆 Predicted Output (milliWatts)", f"{predicted_power:.2f} mW")
            if actual_power is not None:
                col2.metric("📟 Actual Output (milliWatts)", f"{actual_power:.2f} mW")
            else:
                col2.warning("Actual Output not available.")

            st.markdown("---")
            if actual_power is not None:
                if anomaly_detected:
                    st.error(f"⚠️ Anomaly Detected! Difference: {difference:.2f} mW ({diff_percent:.1f}%)")
                else:
                    st.success("✅ System Operating Normally")

            st.markdown("---")
            if "Solar Power" in df.columns and "Timestamp" in df.columns:
                st.markdown("### 📈 Solar Power Output Over Time")
                df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")

                fig = px.line(
                    df,
                    x="Timestamp",
                    y="Solar Power",
                    title="Solar Power Trend",
                    labels={"Solar Power": "Power (mW)", "Timestamp": "Time"},
                    template="plotly_white",
                    markers=True,
                    color_discrete_sequence=["#fbc02d"]
                )
                fig.update_layout(
                    title_font_size=20,
                    margin=dict(l=20, r=20, t=40, b=20),
                    plot_bgcolor="#fffde7"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("No historical solar power data available.")
    else:
        st.error("❌ No data found in the Google Sheet.")
