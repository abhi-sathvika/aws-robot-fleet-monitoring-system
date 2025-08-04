import json
import time
import ssl
import paho.mqtt.client as mqtt
from datetime import datetime
import base64
import random
import threading

class SLAMRobotAWS:
    def __init__(self, endpoint, cert_path, key_path, ca_path, thing_name):
        self.endpoint = endpoint
        self.cert_path = cert_path
        self.key_path = key_path
        self.ca_path = ca_path
        self.thing_name = thing_name
        self.client = None
        self.connected = False
        
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.connected = True
            print(f"✅ Connected to AWS IoT Core! Result code: {rc}")
            
            # Subscribe to command topic
            command_topic = f"slam/{self.thing_name}/commands"
            client.subscribe(command_topic)
            print(f"📡 Subscribed to: {command_topic}")
            
            # Send initial status
            self.publish_status("online")
        else:
            print(f"❌ Failed to connect. Result code: {rc}")
    
    def on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
            print(f"📨 Received command: {payload}")
            
            # Handle different commands
            if payload.get('command') == 'start_mapping':
                print("🗺️ Starting mapping...")
            elif payload.get('command') == 'stop_mapping':
                print("🛑 Stopping mapping...")
                
        except Exception as e:
            print(f"❌ Error processing message: {e}")
    
    def on_disconnect(self, client, userdata, rc):
        self.connected = False
        print(f"📡 Disconnected from AWS IoT Core")
    
    def connect_to_aws(self):
        try:
            # Create MQTT client
            self.client = mqtt.Client(self.thing_name)
            
            # Set callbacks
            self.client.on_connect = self.on_connect
            self.client.on_message = self.on_message
            self.client.on_disconnect = self.on_disconnect
            
            # Configure SSL/TLS
            self.client.tls_set(
                ca_certs=self.ca_path,
                certfile=self.cert_path,
                keyfile=self.key_path,
                cert_reqs=ssl.CERT_REQUIRED,
                tls_version=ssl.PROTOCOL_TLSv1_2,
                ciphers=None
            )
            
            # Connect to AWS IoT Core
            print(f"🔗 Connecting to AWS IoT Core: {self.endpoint}")
            self.client.connect(self.endpoint, 8883, 60)
            
            # Start network loop
            self.client.loop_start()
            
            return True
            
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    def publish_status(self, status):
        """Publish robot status"""
        if not self.connected:
            print("❌ Not connected to AWS")
            return
            
        topic = f"slam/{self.thing_name}/status"
        payload = {
            "robot_id": self.thing_name,
            "status": status,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self.client.publish(topic, json.dumps(payload))
        print(f"📤 Published status: {status}")
    
    def publish_fake_map_data(self):
        """Simulate sending map data"""
        if not self.connected:
            print("❌ Not connected to AWS")
            return
            
        topic = f"slam/{self.thing_name}/map/data"
        
        # Simulate map data
        fake_map_data = {
            "robot_id": self.thing_name,
            "timestamp": datetime.utcnow().isoformat(),
            "position": {
                "x": random.uniform(0, 10),
                "y": random.uniform(0, 10),
                "theta": random.uniform(0, 6.28)
            },
            "map_dimensions": {
                "width": 1000,
                "height": 800
            },
            "map_resolution": 0.05,
            "map_image": base64.b64encode(b"fake_map_image_data").decode()
        }
        
        self.client.publish(topic, json.dumps(fake_map_data))
        print("📤 Published fake map data")
    
    def publish_position_update(self):
        """Publish position update"""
        if not self.connected:
            print("❌ Not connected to AWS")
            return
            
        topic = f"slam/{self.thing_name}/position"
        payload = {
            "robot_id": self.thing_name,
            "position": {
                "x": random.uniform(0, 10),
                "y": random.uniform(0, 10),
                "theta": random.uniform(0, 6.28)
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self.client.publish(topic, json.dumps(payload))
        print("📤 Published position update")

def main():
    # Configuration - UPDATE THESE VALUES!
    ENDPOINT = "a25d63g4uuwfhc-ats.iot.us-east-1.amazonaws.com"  # From IoT Core Settings
    CERT_PATH = "certs/device-certificate.pem.crt"
    KEY_PATH = "certs/private-key.pem.key"
    CA_PATH = "certs/root-ca.pem"
    THING_NAME = "slam-robot-001"
    
    # Create robot client
    robot = SLAMRobotAWS(ENDPOINT, CERT_PATH, KEY_PATH, CA_PATH, THING_NAME)
    
    # Connect to AWS
    if robot.connect_to_aws():
        print("🤖 Robot connected! Starting simulation...")
        
        # Wait for connection
        time.sleep(2)
        
        # Simulate robot behavior
        try:
            while True:
                # Send position update every 5 seconds
                robot.publish_position_update()
                time.sleep(5)
                
                # Send map data every 30 seconds
                robot.publish_fake_map_data()
                time.sleep(25)  # 5 + 25 = 30 seconds total
                
        except KeyboardInterrupt:
            print("\n🛑 Stopping robot...")
            robot.publish_status("offline")
            robot.client.disconnect()
            print("👋 Robot disconnected")
    
    else:
        print("❌ Failed to connect to AWS")

if __name__ == "__main__":
    main()