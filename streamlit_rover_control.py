"""
ESP32 Solar Car Control - Streamlit Web Interface
Deploy this on Streamlit Cloud to control your ESP32 car remotely
"""

import streamlit as st
import paho.mqtt.client as mqtt
import json
import time
from datetime import datetime
import threading
import queue

# MQTT Configuration
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
MQTT_TOPIC_COMMAND = "esp32car/command"
MQTT_TOPIC_STATUS = "esp32car/status"

class MQTTController:
    def __init__(self):
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.status_queue = queue.Queue()
        self.connected = False
        self.last_status = {}
        
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.connected = True
            st.success("Connected to MQTT broker successfully!")
            client.subscribe(MQTT_TOPIC_STATUS)
        else:
            self.connected = False
            st.error(f"Failed to connect to MQTT broker. Code: {rc}")
    
    def on_message(self, client, userdata, msg):
        try:
            status_data = json.loads(msg.payload.decode())
            self.last_status = status_data
            self.status_queue.put(status_data)
        except Exception as e:
            st.error(f"Error processing status message: {e}")
    
    def connect(self):
        try:
            self.client.connect(MQTT_BROKER, MQTT_PORT, 60)
            self.client.loop_start()
            return True
        except Exception as e:
            st.error(f"Connection error: {e}")
            return False
    
    def send_command(self, command, car_id="ALL"):
        if not self.connected:
            st.warning("Not connected to MQTT broker")
            return False
            
        message = {
            "command": command,
            "car_id": car_id,
            "timestamp": int(time.time() * 1000)
        }
        
        try:
            result = self.client.publish(MQTT_TOPIC_COMMAND, json.dumps(message))
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                return True
            else:
                st.error(f"Failed to send command: {result.rc}")
                return False
        except Exception as e:
            st.error(f"Error sending command: {e}")
            return False
    
    def disconnect(self):
        if self.connected:
            self.client.loop_stop()
            self.client.disconnect()
            self.connected = False

# Initialize MQTT controller
if 'mqtt_controller' not in st.session_state:
    st.session_state.mqtt_controller = MQTTController()

# Page configuration
st.set_page_config(
    page_title="ESP32 Solar Car Control",
    page_icon="🚗",
    layout="wide"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #ff6b6b, #4ecdc4);
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        color: white;
        margin-bottom: 2rem;
    }
    
    .control-button {
        width: 100%;
        height: 80px;
        font-size: 20px;
        font-weight: bold;
        border: none;
        border-radius: 10px;
        margin: 5px;
    }
    
    .status-card {
        background: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #4ecdc4;
    }
    
    .emergency-stop {
        background: #ff4444 !important;
        color: white !important;
    }
    
    .movement-btn {
        background: #4ecdc4 !important;
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="main-header">
    <h1>ESP32 Solar Car Remote Control</h1>
    <p>Control your solar-powered 4-wheeler remotely via MQTT</p>
</div>
""", unsafe_allow_html=True)

# Main layout
col1, col2 = st.columns([2, 1])

with col1:
    st.header("Car Controls")
    
    # Connection status and controls
    connection_col1, connection_col2 = st.columns([1, 1])
    
    with connection_col1:
        if st.button("Connect to Car", key="connect_btn"):
            with st.spinner("Connecting to MQTT broker..."):
                if st.session_state.mqtt_controller.connect():
                    time.sleep(2)  # Give time for connection
                    st.experimental_rerun()
    
    with connection_col2:
        if st.button("Disconnect", key="disconnect_btn"):
            st.session_state.mqtt_controller.disconnect()
            st.info("Disconnected from MQTT broker")
            st.experimental_rerun()
    
    # Show connection status
    if st.session_state.mqtt_controller.connected:
        st.success("🟢 Connected to MQTT broker")
    else:
        st.error("🔴 Not connected to MQTT broker")
    
    st.divider()
    
    # Movement controls in a cross pattern
    st.subheader("Movement Controls")
    
    # Create a 3x3 grid for movement controls
    button_cols = st.columns([1, 1, 1])
    
    # Top row - Forward button
    with button_cols[1]:
        if st.button("FORWARD", key="forward", help="Move forward"):
            if st.session_state.mqtt_controller.send_command("FORWARD"):
                st.success("Forward command sent!")
                time.sleep(0.5)
                st.experimental_rerun()
    
    # Middle row - Left, Stop, Right
    button_cols2 = st.columns([1, 1, 1])
    
    with button_cols2[0]:
        if st.button("LEFT", key="left", help="Turn left"):
            if st.session_state.mqtt_controller.send_command("LEFT"):
                st.success("Left command sent!")
                time.sleep(0.5)
                st.experimental_rerun()
    
    with button_cols2[1]:
        if st.button("🛑 STOP", key="stop", help="Emergency stop"):
            if st.session_state.mqtt_controller.send_command("STOP"):
                st.success("Stop command sent!")
                time.sleep(0.5)
                st.experimental_rerun()
    
    with button_cols2[2]:
        if st.button("RIGHT", key="right", help="Turn right"):
            if st.session_state.mqtt_controller.send_command("RIGHT"):
                st.success("Right command sent!")
                time.sleep(0.5)
                st.experimental_rerun()
    
    # Bottom row - Backward button
    button_cols3 = st.columns([1, 1, 1])
    
    with button_cols3[1]:
        if st.button("BACKWARD", key="backward", help="Move backward"):
            if st.session_state.mqtt_controller.send_command("BACKWARD"):
                st.success("Backward command sent!")
                time.sleep(0.5)
                st.experimental_rerun()

with col2:
    st.header("Car Status")
    
    # Auto-refresh toggle
    auto_refresh = st.checkbox("Auto-refresh status", value=True)
    
    if auto_refresh:
        # Auto-refresh every 3 seconds
        placeholder = st.empty()
        if st.session_state.mqtt_controller.connected:
            with placeholder.container():
                if st.session_state.mqtt_controller.last_status:
                    status = st.session_state.mqtt_controller.last_status
                    
                    st.markdown("###Car Information")
                    st.write(f"**Car ID:** `{status.get('car_id', 'Unknown')}`")
                    st.write(f"**Status:** {status.get('status', 'Unknown')}")
                    st.write(f"**Last Command:** `{status.get('command', 'None')}`")
                    
                    st.markdown("###Connection Info")
                    rssi = status.get('wifi_rssi', 0)
                    if rssi > -50:
                        signal_quality = "Excellent"
                        signal_color = "green"
                    elif rssi > -70:
                        signal_quality = "Good"
                        signal_color = "orange"
                    else:
                        signal_quality = "Weak"
                        signal_color = "red"
                    
                    st.write(f"**WiFi Signal:** {rssi} dBm")
                    st.markdown(f"**Signal Quality:** <span style='color:{signal_color}'>{signal_quality}</span>", unsafe_allow_html=True)
                    
                    st.markdown("### ⚙️ System Info")
                    uptime_seconds = status.get('uptime', 0) / 1000
                    uptime_minutes = int(uptime_seconds / 60)
                    uptime_hours = int(uptime_minutes / 60)
                    uptime_display = f"{uptime_hours}h {uptime_minutes%60}m {int(uptime_seconds%60)}s"
                    
                    st.write(f"**Uptime:** {uptime_display}")
                    st.write(f"**Free Memory:** {status.get('free_heap', 0)} bytes")
                    
                    # Last update time
                    last_update = datetime.fromtimestamp(status.get('timestamp', 0) / 1000)
                    st.write(f"**Last Update:** {last_update.strftime('%H:%M:%S')}")
                    
                else:
                    st.info("⏳ Waiting for car status...")
        else:
            st.warning("Connect to view car status")
        
        # Auto-refresh mechanism
        time.sleep(3)
        st.experimental_rerun()
    
    else:
        # Manual refresh
        if st.button("🔄 Refresh Status"):
            st.experimental_rerun()
        
        if st.session_state.mqtt_controller.last_status:
            status = st.session_state.mqtt_controller.last_status
            
            st.markdown("###Car Information")
            st.json(status)

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: #666; padding: 1rem;'>
    <p>ESP32 Solar Car Control Interface | Built with Streamlit & MQTT</p>
    <p>Make sure your ESP32 is powered on and connected to WiFi</p>
</div>
""", unsafe_allow_html=True)

# Sidebar with instructions
with st.sidebar:
    st.header("Instructions")
    
    st.markdown("""
    ### Getting Started:
    1. **Power on** your ESP32 solar car
    2. **Connect** the car to WiFi (it will create a hotspot if needed)
    3. Click **"Connect to Car"** in the main interface
    4. Use the **movement buttons** to control your car
    
    ### Movement Controls:
    - ⬆️ **Forward**: Move straight ahead
    - ⬇️ **Backward**: Move in reverse  
    - ⬅️ **Left**: Turn left (tank turn)
    - ➡️ **Right**: Turn right (tank turn)
    - 🛑 **Stop**: Emergency stop
    
    ### Status Information:
    - **Signal Strength**: WiFi connection quality
    - **Uptime**: How long the car has been running
    - **Memory**: Available system memory
    - **Last Command**: Most recent command executed
    """)
    
    st.markdown("---")
    st.markdown("###Solar Power Tips:")
    st.markdown("""
    - Place the solar panel in direct sunlight
    - Monitor battery levels regularly
    - Use during daylight hours for best performance
    """)
    
    st.markdown("---")
    st.markdown("### 🛠️ Troubleshooting:")
    st.markdown("""
    - **Connection issues**: Check WiFi and restart ESP32
    - **No response**: Verify MQTT broker connection
    - **Slow response**: Check signal strength
    """)

# Auto-cleanup on page close
if st.session_state.get('cleanup_registered', False) is False:
    import atexit
    def cleanup():
        if 'mqtt_controller' in st.session_state:
            st.session_state.mqtt_controller.disconnect()
    atexit.register(cleanup)
    st.session_state.cleanup_registered = True
