import streamlit as st
import paho.mqtt.client as mqtt
import json
import time
import threading
from datetime import datetime

# Configure Streamlit page
st.set_page_config(
    page_title="ESP32 Solar Rover Control",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# MQTT Configuration - Replace with your HiveMQ Cloud details
MQTT_BROKER = "your-hivemq-cloud-url.hivemq.cloud"
MQTT_PORT = 8883
MQTT_USERNAME = "your-mqtt-username" 
MQTT_PASSWORD = "your-mqtt-password"
CLIENT_ID = "streamlit_rover_controller"

# Topics
COMMAND_TOPIC = "rover/command"
STATUS_TOPIC = "rover/status"
BATTERY_TOPIC = "rover/battery"

class RoverController:
    def __init__(self):
        self.client = None
        self.connected = False
        self.rover_status = {}
        self.battery_info = {}
        self.last_update = None

    def setup_mqtt(self):
        """Initialize MQTT client with SSL/TLS"""
        try:
            self.client = mqtt.Client(CLIENT_ID)
            self.client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

            # Enable SSL/TLS
            self.client.tls_set()

            # Set callbacks
            self.client.on_connect = self.on_connect
            self.client.on_message = self.on_message
            self.client.on_disconnect = self.on_disconnect

            # Connect to broker
            self.client.connect(MQTT_BROKER, MQTT_PORT, 60)
            self.client.loop_start()

            return True
        except Exception as e:
            st.error(f"MQTT Connection Error: {str(e)}")
            return False

    def on_connect(self, client, userdata, flags, rc):
        """Callback for successful MQTT connection"""
        if rc == 0:
            self.connected = True
            client.subscribe(STATUS_TOPIC)
            client.subscribe(BATTERY_TOPIC)
        else:
            self.connected = False

    def on_message(self, client, userdata, msg):
        """Callback for received MQTT messages"""
        try:
            payload = json.loads(msg.payload.decode())

            if msg.topic == STATUS_TOPIC:
                self.rover_status = payload
                self.last_update = datetime.now()
            elif msg.topic == BATTERY_TOPIC:
                self.battery_info = payload

        except json.JSONDecodeError:
            pass

    def on_disconnect(self, client, userdata, rc):
        """Callback for MQTT disconnection"""
        self.connected = False

    def send_command(self, command, speed=150):
        """Send movement command to rover"""
        if self.client and self.connected:
            message = {
                "command": command,
                "speed": speed,
                "timestamp": time.time()
            }
            self.client.publish(COMMAND_TOPIC, json.dumps(message))
            return True
        return False

# Initialize rover controller
if 'rover' not in st.session_state:
    st.session_state.rover = RoverController()
    st.session_state.rover.setup_mqtt()

rover = st.session_state.rover

# Custom CSS for styling
st.markdown("""
<style>
    .big-button {
        font-size: 20px !important;
        height: 3rem !important;
        width: 100% !important;
        margin: 5px 0 !important;
    }

    .status-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        margin: 10px 0;
    }

    .online-status {
        color: #00ff00;
        font-weight: bold;
    }

    .offline-status {
        color: #ff0000;
        font-weight: bold;
    }

    .battery-good {
        color: #00aa00;
    }

    .battery-warning {
        color: #ff8800;
    }

    .battery-critical {
        color: #ff0000;
    }
</style>
""", unsafe_allow_html=True)

# Main title and header
st.title("🤖 ESP32 Solar Rover Control Dashboard")
st.markdown("*Remote control your solar-powered rover via MQTT*")

# Sidebar for settings and status
st.sidebar.title("🔧 Control Panel")

# Connection status
if rover.connected:
    st.sidebar.markdown('<div class="online-status">🟢 Connected to Rover</div>', unsafe_allow_html=True)
else:
    st.sidebar.markdown('<div class="offline-status">🔴 Disconnected</div>', unsafe_allow_html=True)
    if st.sidebar.button("🔄 Reconnect"):
        rover.setup_mqtt()

# Speed control
st.sidebar.subheader("⚡ Speed Control")
speed = st.sidebar.slider("Motor Speed", 0, 255, 150, 5)

# Emergency stop
if st.sidebar.button("🛑 EMERGENCY STOP", type="primary"):
    rover.send_command("stop", 0)

# Main control area
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    st.subheader("🎮 Movement Controls")

    # Forward button
    if st.button("⬆️ FORWARD", key="forward", help="Move rover forward"):
        if rover.send_command("forward", speed):
            st.success("Moving forward...")
        else:
            st.error("Failed to send command")

    # Left and Right buttons
    col_left, col_right = st.columns(2)
    with col_left:
        if st.button("⬅️ LEFT", key="left", help="Turn rover left"):
            if rover.send_command("left", speed):
                st.success("Turning left...")
            else:
                st.error("Failed to send command")

    with col_right:
        if st.button("➡️ RIGHT", key="right", help="Turn rover right"):
            if rover.send_command("right", speed):
                st.success("Turning right...")
            else:
                st.error("Failed to send command")

    # Backward button
    if st.button("⬇️ BACKWARD", key="backward", help="Move rover backward"):
        if rover.send_command("backward", speed):
            st.success("Moving backward...")
        else:
            st.error("Failed to send command")

    # Stop button
    if st.button("⏹️ STOP", key="stop", help="Stop rover"):
        if rover.send_command("stop", 0):
            st.success("Rover stopped")
        else:
            st.error("Failed to send command")

# Status information
st.markdown("---")
st.subheader("📊 Rover Status")

status_col1, status_col2 = st.columns(2)

with status_col1:
    st.markdown("### 📡 System Status")

    if rover.rover_status:
        status_data = rover.rover_status

        # Connection status
        st.metric("Connection", "🟢 Online" if rover.connected else "🔴 Offline")

        # Last command
        if 'last_command' in status_data:
            st.metric("Last Command", status_data['last_command'])

        # Current speed
        if 'speed' in status_data:
            st.metric("Current Speed", f"{status_data['speed']}/255")

        # WiFi signal strength
        if 'wifi_rssi' in status_data:
            rssi = status_data['wifi_rssi']
            signal_quality = "Excellent" if rssi > -50 else "Good" if rssi > -70 else "Poor"
            st.metric("WiFi Signal", f"{rssi} dBm ({signal_quality})")

        # Uptime
        if 'uptime' in status_data:
            uptime_seconds = status_data['uptime'] / 1000
            uptime_minutes = int(uptime_seconds / 60)
            st.metric("Uptime", f"{uptime_minutes} minutes")

        # Memory usage
        if 'free_heap' in status_data:
            heap_kb = status_data['free_heap'] / 1024
            st.metric("Free Memory", f"{heap_kb:.1f} KB")

    else:
        st.warning("No rover status data received")

with status_col2:
    st.markdown("### 🔋 Battery Status")

    if rover.battery_info:
        battery_data = rover.battery_info

        # Battery percentage
        if 'battery_percentage' in battery_data:
            percentage = battery_data['battery_percentage']
            if percentage > 50:
                st.markdown(f'<div class="battery-good">🔋 {percentage}%</div>', unsafe_allow_html=True)
            elif percentage > 20:
                st.markdown(f'<div class="battery-warning">🔋 {percentage}%</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="battery-critical">🔋 {percentage}%</div>', unsafe_allow_html=True)

        # Battery voltage
        if 'battery_voltage' in battery_data:
            voltage = battery_data['battery_voltage']
            st.metric("Voltage", f"{voltage:.2f} V")

        # Charging status
        if 'charging' in battery_data:
            charging = battery_data['charging']
            charge_status = "🔌 Charging" if charging else "🔋 Discharging"
            st.metric("Status", charge_status)

    else:
        st.warning("No battery data received")

# Auto-refresh
if rover.last_update:
    seconds_since_update = (datetime.now() - rover.last_update).total_seconds()
    if seconds_since_update > 30:
        st.warning(f"⚠️ No updates received for {int(seconds_since_update)} seconds")

# Add refresh button
if st.button("🔄 Refresh Status"):
    st.experimental_rerun()

# Information section
st.markdown("---")
with st.expander("ℹ️ How to Use"):
    st.markdown("""
    ### Getting Started:

    1. **Setup WiFi**: Power on your rover and connect to the "ESP32-Rover" WiFi network
    2. **Configure Network**: Go to 192.168.4.1 and enter your WiFi credentials
    3. **MQTT Connection**: Ensure your MQTT broker settings are correct in the code
    4. **Control**: Use the movement buttons to control your rover remotely

    ### Features:
    - **Real-time Control**: Send commands instantly via MQTT
    - **Status Monitoring**: View rover status, battery level, and connection quality
    - **Speed Control**: Adjust motor speed with the slider
    - **Emergency Stop**: Immediately stop the rover if needed

    ### Troubleshooting:
    - **Connection Issues**: Check WiFi and MQTT broker settings
    - **Slow Response**: Verify WiFi signal strength and MQTT connection
    - **Battery Low**: Ensure solar panel is receiving adequate sunlight
    """)

with st.expander("⚙️ Technical Details"):
    st.markdown("""
    ### System Architecture:
    - **Microcontroller**: ESP32 with WiFi capability
    - **Communication**: MQTT over TLS/SSL via HiveMQ Cloud
    - **Motor Control**: L298N dual H-bridge driver
    - **Display**: 0.96" OLED with animated eyes
    - **Power**: Solar panel with Li-ion battery backup

    ### MQTT Topics:
    - `rover/command`: Movement commands
    - `rover/status`: System status updates
    - `rover/battery`: Battery monitoring data
    """)

# Footer
st.markdown("---")
st.markdown("*Built with Streamlit and ESP32 - No soldering required! 🔧*")
