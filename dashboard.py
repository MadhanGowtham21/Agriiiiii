import streamlit as st
import pandas as pd
import numpy as np
import requests
from twilio.rest import Client
from datetime import datetime
import re
import matplotlib.pyplot as plt
import joblib
import seaborn as sns

# ThingSpeak API
CHANNEL_ID = "2882231"
READ_API_KEY = "SZDS98NDZ0CWNLVY"


# Twilio Configuration
TWILIO_PHONE_NUMBER = "whatsapp:+14155238886"  # Your Twilio WhatsApp number
AUTH_TOKEN = "45776c7969fdb25c99f0c14f24190fef"  # Your Twilio Auth Token
SID = "AC733c2e5c779814fd77a4b5a4ffb618e9"  # Your Twilio SID
client = Client(SID, AUTH_TOKEN)

# Session State Initialization
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'password' not in st.session_state:
    st.session_state.password = "admin123"
if 'theme' not in st.session_state:
    st.session_state.theme = "Light"
if 'language' not in st.session_state:
    st.session_state.language = "English"

# Language support
def t(text):
    tamil_dict = {
        "Login": "உள்நுழைய",
        "Username": "பயனர் பெயர்",
        "Password": "கடவுச்சொல்",
        "Login Successful": "உள்நுழைவு வெற்றிகரமாக முடிந்தது",
        "Invalid Credentials": "தவறான தகவல்கள்",
        "Smart Agriculture Dashboard": "スマート வேளாண்மை டாஷ்போர்டு",
        "Navigation": "வழிசெலுத்தல்",
        "Home": "முகப்பு",
        "Sensor Visualization": "அணுகி தரவுகள்",
        "Threshold Alerts": "அவதானிப்பு அலாரங்கள்",
        "Settings": "அமைப்புகள்",
        "Logout": "வெளியேறு",
        "Welcome to the Smart Agriculture Monitoring System!": "スマート வேளாண்மை கண்காணிப்பு முறைமைக்கு வரவேற்கிறோம்!",
        "Set Threshold Alerts": "அவதானிப்பு அலாரங்களை அமைக்கவும்",
        "Check Alerts": "அலாரங்களை சரிபார்க்கவும்",
        "Language": "மொழி",
        "Theme": "தீம்",
        "Change Password": "கடவுச்சொல் மாற்றவும்",
        "Current Password": "தற்போதைய கடவுச்சொல்",
        "New Password": "புதிய கடவுச்சொல்",
        "Update Password": "கடவுச்சொல் புதுப்பிக்கவும்",
        "Apply Settings": "அமைப்புகளை செயல்படுத்து",
        "Download CSV": "CSV பதிவிறக்குக",
        "Sensor Data": "அணுகி தரவுகள்",
        "Date": "தேதி",
        "Time": "நேரம்",
    }
    return tamil_dict.get(text, text) if st.session_state.language == "Tamil" else text

# Chatbot pairs
pairs = [
    (r"Hi|Hello|Hey", ["Hello! How can I assist you with the Smart Agriculture System today?"]),
    (r"Tell me about the Smart Agriculture System",
     [
         "The Smart Agriculture Monitoring System helps farmers monitor conditions like temperature, humidity, soil moisture, and more using sensors."]),
    (r"What is the flame sensor?",
     ["The flame sensor detects fire or flame in the environment and helps alert the system in case of a fire."]),
    (r"What is soil moisture?",
     ["Soil moisture refers to the amount of water present in the soil, which is essential for plant health."]),
    (r"How do I set alerts?",
     [
         "You can set alerts for various sensors like flame, soil moisture, distance, etc., in the 'Threshold Alerts' section of the dashboard."]),
    (r"Bye|Goodbye", ["Goodbye! Have a great day!"]),
    (r"(.*)", ["Sorry, I didn't understand that. Can you please clarify?"]),

    # Additional pairs:
    (r"What is temperature monitoring?",
     [
         "Temperature monitoring allows you to track the environmental temperature in your farming area, which is crucial for crop health."]),
    (r"What is humidity?",
     [
         "Humidity refers to the amount of moisture in the air. It is an important factor in agricultural growth and affects plant transpiration."]),
    (r"How does the water level sensor work?",
     [
         "The water level sensor helps monitor the level of water in fields or irrigation systems to ensure proper irrigation and water usage."]),
    (r"Can I get real-time sensor data?",
     [
         "Yes! You can view real-time data from various sensors like temperature, humidity, and soil moisture on the dashboard."]),
    (r"What is the distance sensor for?",
     [
         "The distance sensor is used to measure the distance of objects or obstacles, useful for monitoring the environment or detecting obstacles in irrigation systems."]),
    (r"Tell me more about the soil moisture sensor",
     [
         "The soil moisture sensor measures the moisture level in the soil to help optimize irrigation and ensure the soil is at the right moisture level for plant growth."]),
    (r"How can I download sensor data?",
     [
         "You can download the sensor data in CSV format by clicking on the 'Download CSV' button available in the 'Sensor Visualization' section."]),
    (r"How do I change the system language?",
     ["You can change the language in the 'Settings' section of the dashboard by selecting your preferred language."]),
    (r"How do I change the system theme?",
     ["You can change the system theme (Light or Dark) in the 'Settings' section of the dashboard."]),
    (r"What is the role of the humidity sensor?",
     [
         "The humidity sensor tracks the moisture level in the air, helping to monitor environmental conditions for plant growth."]),
    (r"How do I receive alerts for sensor values?",
     [
         "You will receive alerts via SMS when a sensor value exceeds the defined threshold in the 'Threshold Alerts' section."]),
    (r"Can I monitor multiple fields?",
     [
         "Yes, you can monitor multiple fields as long as each field is equipped with the necessary sensors to provide real-time data."]),
    (r"Where can I view historical sensor data?",
     [
         "You can view historical data on the dashboard, where you can see past sensor readings and download them for further analysis."]),
    (r"What happens if the flame sensor detects a high level?",
     [
         "If the flame sensor detects a high level of flame, it will trigger an alert to notify you of a potential fire hazard."]),
    (r"Why is soil moisture important?",
     [
         "Soil moisture is crucial for maintaining optimal water levels for plants. Too little moisture can lead to drought stress, while too much can cause root rot."]),
    (r"How does the system help farmers?",
     [
         "The system helps farmers by providing real-time monitoring of environmental factors, allowing them to make informed decisions about irrigation, fertilization, and other farming practices."]),
    (r"How can I set up a distance threshold?",
     [
         "You can set a distance threshold by navigating to the 'Threshold Alerts' section in the dashboard and adjusting the slider for the distance sensor."]),
]


# Function to get chatbot response
def chatbot_response(user_input):
    for pattern, responses in pairs:
        if re.match(pattern, user_input, re.I):
            return responses[0]
    return "Sorry, I didn't understand that. Can you please clarify?"

# Fetch data from ThingSpeak
def fetch_data():
    url = f"https://api.thingspeak.com/channels/{CHANNEL_ID}/feeds.json?api_key={READ_API_KEY}&results=10"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()["feeds"]
        df = pd.DataFrame(data)
        df = df.rename(columns={
            'field1': 'Temperature',
            'field2': 'Humidity',
            'field3': 'Distance',
            'field4': 'Rain Level',
            'field5': 'Soil Moisture',
            'field6': 'Flame',
            'field7': 'Light',
            'field8': 'Water Level'
        })
        df['created_at'] = pd.to_datetime(df['created_at'])
        df.set_index('created_at', inplace=True)
        return df
    else:
        st.error("❌ Failed to fetch data from ThingSpeak")
        return None

# Send Twilio Alert
def send_whatsapp_alert(to, message):
    try:
        message = client.messages.create(
            body=message,
            from_=TWILIO_PHONE_NUMBER,
            to=to
        )
        st.success(f"Alert sent to {to}: {message}")
    except Exception as e:
        st.error(f"Failed to send message: {e}")

# Login Page
def login_page():
    st.title(t("Login"))
    username = st.text_input(t("Username"))
    password = st.text_input(t("Password"), type="password")
    if st.button(t("Login")):
        if username == "admin" and password == st.session_state.password:
            st.session_state.logged_in = True
            st.success(t("Login Successful"))
            st.rerun()
        else:
            st.error(t("Invalid Credentials"))

# App Pages
def data_analytics():
    st.title("📊 Data Analytics")

    # Fetch real-time data from ThingSpeak using your existing fetch_data function
    df = fetch_data()

    if df is not None:
        # Convert all relevant columns to numeric (in case they are strings)
        df['Temperature'] = pd.to_numeric(df['Temperature'], errors='coerce')
        df['Humidity'] = pd.to_numeric(df['Humidity'], errors='coerce')
        df['Soil Moisture'] = pd.to_numeric(df['Soil Moisture'], errors='coerce')
        df['Rain Level'] = pd.to_numeric(df['Rain Level'], errors='coerce')
        df['Flame'] = pd.to_numeric(df['Flame'], errors='coerce')
        df['Light'] = pd.to_numeric(df['Light'], errors='coerce')
        df['Water Level'] = pd.to_numeric(df['Water Level'], errors='coerce')

        # Drop rows with missing data in the columns of interest
        df = df.dropna(subset=['Temperature', 'Humidity', 'Soil Moisture', 'Rain Level', 'Flame'])

        st.subheader("📈 Sensor Data Analytics")

        # Options for analysis (you can add more options based on your needs)
        analysis_option = st.selectbox(
            "Choose Analysis Type",
            ["Temperature Trends", "Humidity Trends", "Soil Moisture Analysis", "Rain Level Analysis", "Flame Sensor Events"]
        )

        # Perform analysis based on the option selected
        if analysis_option == "Temperature Trends":
            st.subheader("🌡️ Temperature Trends")
            st.write("Analyzing the temperature trends over time.")
            fig, ax = plt.subplots()
            df['Temperature'].plot(ax=ax, color='red')
            ax.set_title("Temperature Over Time")
            ax.set_ylabel("Temperature (°C)")
            st.pyplot(fig)

        elif analysis_option == "Humidity Trends":
            st.subheader("💧 Humidity Trends")
            st.write("Analyzing the humidity trends over time.")
            fig, ax = plt.subplots()
            df['Humidity'].plot(ax=ax, color='blue')
            ax.set_title("Humidity Over Time")
            ax.set_ylabel("Humidity (%)")
            st.pyplot(fig)

        elif analysis_option == "Soil Moisture Analysis":
            st.subheader("🌱 Soil Moisture Analysis")
            st.write("Analyzing soil moisture levels over time.")
            fig, ax = plt.subplots()
            df['Soil Moisture'].plot(ax=ax, color='green')
            ax.set_title("Soil Moisture Levels Over Time")
            ax.set_ylabel("Soil Moisture (%)")
            st.pyplot(fig)

        elif analysis_option == "Rain Level Analysis":
            st.subheader("🌧️ Rain Level Analysis")
            st.write("Analyzing rain levels over time.")
            fig, ax = plt.subplots()
            df['Rain Level'].plot(ax=ax, color='purple')
            ax.set_title("Rain Level Over Time")
            ax.set_ylabel("Rain Level")
            st.pyplot(fig)

        elif analysis_option == "Flame Sensor Events":
            st.subheader("🔥 Flame Sensor Events")
            st.write("Visualizing flame sensor events.")
            # Assuming flame sensor detects when its value is > 0
            flame_events = df[df['Flame'] > 0]  # Filter where flame is detected
            st.write(f"Found {len(flame_events)} flame events.")
            st.dataframe(flame_events)

        # Option to download analytics data
        if st.button("Download Analytics Data"):
            st.download_button(
                label="📥 Download Analytics Data",
                data=df.to_csv().encode('utf-8'),
                file_name="analytics_data.csv",
                mime="text/csv"
            )


def about_section():
    st.title("🔍 About This Project")

    st.subheader("Project Overview")
    st.write("""
        This project is designed to monitor and automate various aspects of environmental conditions, including temperature, humidity, soil moisture, flame detection, and more. 
        The system uses a combination of sensors to collect real-time data, which is then processed and displayed for analysis. In addition, the system includes automated irrigation and refill mechanisms controlled by motors.

        The project also integrates with IoT capabilities to send and receive data remotely via ThingSpeak, enabling real-time updates and remote monitoring.

        The system is ideal for use in smart farming, environmental monitoring, or any application that requires constant observation of environmental factors.
    """)

    st.subheader("🔧 Components Used")
    st.write("""
        - **Arduino Uno**: The main microcontroller used to interface with sensors and control devices.
        - **ESP8266**: Used for Wi-Fi connectivity, enabling remote data transmission and reception via ThingSpeak.

        **Sensors:**
        - **DHT Sensor**: Used for temperature and humidity measurement.
        - **IR Sensor**: Detects flame and objects.
        - **Water Level Sensor**: Monitors water levels in tanks or reservoirs.
        - **Ultrasonic Sensor**: Measures water distance to assess the depth of water in tanks or reservoirs.
        - **Gas Sensor**: Detects gas leaks or hazardous gases.
        - **Rain Detect Sensor**: Detects rainfall to trigger irrigation system or alert.
        - **LDR Sensor**: Light-dependent resistor, used for measuring light intensity, often for controlling systems like irrigation based on sunlight.

        **Power Supply:**
        - **12V Transformer**: Powers the entire system, including sensors, motors, and controllers.

        **Motors and Motor Drivers:**
        - **Motor Driver**: Used to control the irrigation motor and refill motor for automated control based on sensor inputs.
    """)

    st.subheader("⚙️ Working of the System")
    st.write("""
        The system works by continuously monitoring environmental factors through the sensors. The data collected is processed by the Arduino Uno and sent to the cloud via the ESP8266 for further analysis and visualization on platforms like ThingSpeak.

        Based on the data received, the system can trigger actions like turning on irrigation motors if the soil moisture level is too low, or activating a refill motor when water levels are detected to be too low.

        The flame detection sensor and gas sensor add a layer of safety to the system, enabling alerts in case of dangerous conditions.
    """)


# Load the pre-trained AI model
model = joblib.load('irrigation_model.pkl')

# AI Prediction Section in Streamlit
def ai_prediction():
    st.title("🔮 AI Prediction for Irrigation Needs")

    # Fetch real-time data from ThingSpeak
    data = fetch_data()

    if data is not None:
        st.subheader("Real-Time Sensor Data")
        st.write(data)  # Show the latest sensor data

        # Prepare data for prediction
        features = data[['Temperature', 'Humidity', 'Soil Moisture', 'Rain Level', 'Water Level', 'Flame', 'Light']]

        # Make predictions using the trained model
        prediction = model.predict(features)

        # Show prediction
        if prediction[0] == 1:
            st.success("🚨 Irrigation is needed! 🌾")
        else:
            st.success("✅ No irrigation needed at the moment.")

        # Check if model supports predict_proba with two classes
        if hasattr(model, "predict_proba"):
            prob = model.predict_proba(features)
            if len(model.classes_) > 1:
                index = list(model.classes_).index(1)
                st.write(f"Prediction probability for irrigation needed: {prob[0][index] * 100:.2f}%")
            else:
                st.info("Model does not support multiple class probabilities.")

def electricity_consumption():
    st.title("⚡ Electricity Consumption Monitor")

    df = fetch_data()
    if df is None or df.empty:
        st.warning("No data available.")
        return

    # Filter last 10 entries
    recent_data = df.tail(10)

    refill_motor_on_time = 0  # seconds
    irrigation_motor_on_time = 0  # seconds
    interval = 15  # assuming each reading is 15 seconds apart

    for _, row in recent_data.iterrows():
        if float(row['Distance']) < 10:
            refill_motor_on_time += interval
        if float(row['Soil Moisture']) > 300:
            irrigation_motor_on_time += interval

    # Convert seconds to hours
    refill_time_hr = refill_motor_on_time / 3600
    irrigation_time_hr = irrigation_motor_on_time / 3600

    # Power Consumption in kWh
    refill_power = 50  # Watts
    irrigation_power = 60  # Watts
    refill_kwh = (refill_power * refill_time_hr) / 1000
    irrigation_kwh = (irrigation_power * irrigation_time_hr) / 1000

    # Cost calculation
    unit_rate = 8  # ₹ per unit
    refill_cost = refill_kwh * unit_rate
    irrigation_cost = irrigation_kwh * unit_rate

    # Current calculation
    voltage = 12
    refill_current = refill_power / voltage
    irrigation_current = irrigation_power / voltage

    # Display
    st.subheader("💧 Refill Motor")
    st.write(f"ON Time: {refill_motor_on_time} seconds")
    st.write(f"Power Consumed: {refill_kwh:.4f} kWh")
    st.write(f"Current Usage: {refill_current:.2f} A")
    st.write(f"Cost: ₹{refill_cost:.2f}")

    st.subheader("🌱 Irrigation Motor")
    st.write(f"ON Time: {irrigation_motor_on_time} seconds")
    st.write(f"Power Consumed: {irrigation_kwh:.4f} kWh")
    st.write(f"Current Usage: {irrigation_current:.2f} A")
    st.write(f"Cost: ₹{irrigation_cost:.2f}")

    st.success(f"💰 Total Estimated Cost: ₹{refill_cost + irrigation_cost:.2f}")

def dashboard():
    st.set_page_config(page_title="Smart Agri Dashboard", layout="wide")
    if st.session_state.theme == "Dark":
        st.markdown("<style>body { background-color: #0e1117; color: white; }</style>", unsafe_allow_html=True)

    st.sidebar.title("🌾 " + t("Smart Agriculture Dashboard"))
    menu = [
        f"🌱 {t('Home')}",
        f"📊 {t('Sensor Visualization')}",
        f"🚨 {t('Threshold Alerts')}",
        f"📊 {t('Data Analytics')}",  # New section
        f"🔮 {t('AI Prediction')}",  # Add the AI Prediction section
        f"⚡  {t('Electricity Consumption')}",
        f"🔍 {t('About This Project')}",
        f"⚙️ {t('Settings')}",
        f"🔓 {t('Logout')}"
    ]

    choice = st.sidebar.radio(t("Navigation"), menu)

    if choice.endswith(t("Home")):
        st.title("🌱 " + t("Home"))

        # Product Description
        st.subheader("🚜 " + t("Product Description"))
        st.write(
            "Welcome to our **Smart Agriculture Monitoring System**. This system helps monitor various agricultural conditions such as temperature, humidity, soil moisture, rain level, flame detection, and more. It helps farmers stay informed and take timely actions based on sensor data.")

        # Contact Details
        st.subheader("📞 " + t("Contact Us"))
        st.write("""
            **Support Team:**
            - Email: projectiot2k25@gmail.com
            - Phone: +91 9344789554
            - Address: Palayamkottai Road, Tuticorin District, Tiruchendur, Tamil Nadu 628215
        """)

        # Real-time Sensor Data
        df = fetch_data()
        if df is not None:
            st.subheader("📊 " + t("Real-Time Sensor Data"))

            # Horizontal layout for real-time monitoring
            cols = st.columns(4)
            latest_data = df.iloc[-1]  # Get the latest data from the dataframe

            sensors = [
                "Temperature", "Humidity", "Distance", "Rain Level",
                "Soil Moisture", "Flame", "Light", "Water Level"
            ]
            for i, sensor in enumerate(sensors):
                with cols[i % 4]:
                    value = latest_data[sensor]
                    st.metric(sensor, f"{value}")

        # Display date and time of data retrieval
        st.write("---")
        st.metric("Date", datetime.now().strftime("%Y-%m-%d"))
        st.metric("Time", datetime.now().strftime("%H:%M:%S"))

        # Chatbot section
        st.subheader("🤖 " + t("Chat with our Assistant"))
        user_input = st.text_input("Ask me anything about the Smart Agriculture System:")
        if user_input:
            response = chatbot_response(user_input)
            st.write(f"Bot: {response}")

    elif choice.endswith(t("Sensor Visualization")):
        st.title("📊 " + t("Sensor Visualization"))
        df = fetch_data()
        if df is not None:
            sensors = ['Temperature', 'Humidity', 'Distance', 'Rain Level', 'Soil Moisture', 'Flame', 'Light',
                       'Water Level']
            cols = st.columns(4)
            for i, sensor in enumerate(sensors):
                with cols[i % 4]:
                    if st.button(f"📈 {sensor}"):
                        st.session_state.selected_sensor = sensor
                        st.session_state.df = df
                        st.rerun()

            st.write("---")
            if st.button(t("Download CSV")):
                st.download_button(
                    label="📥 " + t("Download CSV"),
                    data=df.to_csv().encode('utf-8'),
                    file_name="sensor_data.csv",
                    mime="text/csv"
                )

            if 'selected_sensor' in st.session_state:
                selected_sensor = st.session_state.selected_sensor
                df = st.session_state.df
                st.subheader(f"{selected_sensor} Data")
                st.line_chart(df[selected_sensor])
                latest_value = df[selected_sensor].iloc[-1]

                if selected_sensor == "Flame" and latest_value > 1:
                    st.error(f"🔥 {selected_sensor} is too high! Value: {latest_value}")
                elif selected_sensor == "Soil Moisture" and latest_value < 30:
                    st.warning(f"💧 {selected_sensor} is low. Value: {latest_value}")
                else:
                    st.success(f"✅ {selected_sensor} value is normal: {latest_value}")

    elif choice.endswith(t("Data Analytics")):
        data_analytics()  # Call the function to display the data analytics section

    elif choice.endswith(t("AI Prediction")):
        ai_prediction()

    elif choice.endswith(t("Electricity Consumption")):
        electricity_consumption()

    elif choice.endswith(t("About This Project")):
        about_section()

    elif choice.endswith(t("Threshold Alerts")):
        st.title("🚨" + ("Threshold Alerts"))

        # Set Alert Thresholds
        st.markdown("### 🔧 Set Alert Thresholds")
        temperature_threshold = st.number_input("Temperature Threshold", min_value=0.0, max_value=100.0, value=37.0)
        humidity_threshold = st.number_input("Humidity Threshold", min_value=0.0, max_value=100.0, value=80.0)
        flame_threshold = st.number_input("Flame Threshold", min_value=0.0, max_value=1.0, value=1.0)

        # Contact Information
        st.markdown("### 📞 Set Up WhatsApp Alert")
        to_whatsapp = st.text_input("Enter WhatsApp Number to Send Alerts", value="whatsapp:+919344789554")
        message = st.text_area("Enter Alert Message",
                               value="Alert! Sensor threshold exceeded. Please check the system.")

        if st.button("Send Test Alert"):
            send_whatsapp_alert(to_whatsapp, message)

        data = fetch_data()
        # Real-time Alert Logic
        if not data.empty:
            latest = data.iloc[-1]

            try:
                flame = float(latest["Flame"])
                temp = float(latest["Temperature"])
                humidity = float(latest["Humidity"])
            except (ValueError, TypeError):
                st.warning("Sensor data contains invalid values.")
                return

            # Fire Alert
            if flame > flame_threshold:
                send_whatsapp_alert(to_whatsapp, f"🚨 FIRE ALERT DETECTED! Current Flame: {flame}")

            # Temperature Alert
            if temp > temperature_threshold:
                send_whatsapp_alert(to_whatsapp, f"⚠️ High Temperature Alert! Current Temp: {temp}°C")

            # Humidity Alert
            if humidity > humidity_threshold:
                send_whatsapp_alert(to_whatsapp, f"⚠️ High Humidity Alert! Current Humidity: {humidity}%")

        else:
            st.warning("No data available for alert evaluation.")


    elif choice.endswith(t("About The Project")):
        about_section()

    elif choice.endswith(t("Settings")):
        st.title("⚙️ " + t("Settings"))
        st.subheader(t("Change Theme"))
        theme = st.radio(t("Theme"), ["Light", "Dark"])
        st.session_state.theme = theme

        st.subheader(t("Change Language"))
        language = st.radio(t("Language"), ["English", "Tamil"])
        st.session_state.language = language

        st.subheader(t("Change Password"))
        current_password = st.text_input(t("Current Password"), type="password")
        new_password = st.text_input(t("New Password"), type="password")
        if st.button(t("Update Password")):
            if current_password == st.session_state.password:
                st.session_state.password = new_password
                st.success(t("Password Updated"))
            else:
                st.error(t("Incorrect Current Password"))




    elif choice.endswith(t("Logout")):
        st.session_state.logged_in = False
        st.success(t("Logged out successfully"))
        st.rerun()


# Main Program
if not st.session_state.logged_in:
    login_page()
else:
    dashboard()


