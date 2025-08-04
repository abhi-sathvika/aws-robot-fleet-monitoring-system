import json
import datetime
import boto3
from decimal import Decimal

# Initialize AWS services
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('RobotSensorData')  # We'll create this table

def lambda_handler(event, context):
    """
    Enhanced IoT data processor with DynamoDB storage and analytics
    Perfect for demo/portfolio purposes
    """
    
    try:
        # Log the raw event
        print(f"🤖 Received robot data: {json.dumps(event)}")
        
        # Extract timestamp and create unique ID
        timestamp = datetime.datetime.utcnow().isoformat()
        
        # Extract sensor data from event
        sensor_data = event
        robot_id = sensor_data.get('robot_id', 'unknown-robot')
        
        # Process and enhance the data
        processed_data = {
            'robot_id': robot_id,
            'timestamp': timestamp,
            'raw_data': sensor_data
        }
        
        # Temperature processing
        if 'temperature' in sensor_data:
            temp_c = sensor_data['temperature']
            temp_f = (temp_c * 9/5) + 32
            processed_data['temperature_celsius'] = temp_c
            processed_data['temperature_fahrenheit'] = round(temp_f, 1)
            
            # Temperature alerts
            if temp_c > 30:
                processed_data['temperature_alert'] = 'HIGH_TEMPERATURE'
                print(f"🔥 HIGH TEMP ALERT: {temp_c}°C")
            elif temp_c < 10:
                processed_data['temperature_alert'] = 'LOW_TEMPERATURE'
                print(f"🧊 LOW TEMP ALERT: {temp_c}°C")
            
            print(f"🌡️ Temperature: {temp_c}°C ({temp_f:.1f}°F)")
        
        # Humidity processing
        if 'humidity' in sensor_data:
            humidity = sensor_data['humidity']
            processed_data['humidity'] = humidity
            
            if humidity > 80:
                processed_data['humidity_alert'] = 'HIGH_HUMIDITY'
                print(f"💧 HIGH HUMIDITY ALERT: {humidity}%")
            elif humidity < 20:
                processed_data['humidity_alert'] = 'LOW_HUMIDITY'
                print(f"🏜️ LOW HUMIDITY ALERT: {humidity}%")
            
            print(f"💧 Humidity: {humidity}%")
        
        # Distance/Obstacle processing
        if 'distance' in sensor_data:
            distance = sensor_data['distance']
            processed_data['distance'] = distance
            
            if distance < 20:
                processed_data['obstacle_alert'] = 'OBSTACLE_DETECTED'
                processed_data['risk_level'] = 'HIGH'
                print(f"⚠️ OBSTACLE ALERT: {distance}cm - IMMEDIATE ACTION REQUIRED")
            elif distance < 50:
                processed_data['risk_level'] = 'MEDIUM'
                print(f"⚡ CAUTION: Object at {distance}cm")
            else:
                processed_data['risk_level'] = 'LOW'
            
            print(f"📏 Distance: {distance}cm")
        
        # Light level processing
        if 'light' in sensor_data:
            light = sensor_data['light']
            processed_data['light_level'] = light
            
            if light > 700:
                processed_data['lighting_condition'] = 'BRIGHT'
            elif light > 300:
                processed_data['lighting_condition'] = 'NORMAL'
            elif light > 100:
                processed_data['lighting_condition'] = 'DIM'
            else:
                processed_data['lighting_condition'] = 'DARK'
                processed_data['lighting_alert'] = 'LOW_LIGHT_WARNING'
                print(f"🔦 LOW LIGHT WARNING: {light} lux")
            
            print(f"💡 Light: {light} lux ({processed_data['lighting_condition']})")
        
        # Motion processing
        if 'motion' in sensor_data:
            motion = sensor_data['motion']
            processed_data['motion_detected'] = motion
            
            if motion:
                processed_data['activity_status'] = 'ACTIVE'
                print(f"🏃 MOTION DETECTED - Robot is active")
            else:
                processed_data['activity_status'] = 'STATIONARY'
            
            print(f"🏃 Motion: {'Detected' if motion else 'None'}")
        
        # Battery monitoring
        if 'battery' in sensor_data:
            battery = sensor_data['battery']
            processed_data['battery_level'] = battery
            
            if battery < 20:
                processed_data['battery_alert'] = 'CRITICAL_BATTERY'
                print(f"🔋 CRITICAL BATTERY: {battery}% - RETURN TO CHARGING STATION")
            elif battery < 30:
                processed_data['battery_alert'] = 'LOW_BATTERY'
                print(f"🔋 LOW BATTERY WARNING: {battery}%")
            
            print(f"🔋 Battery: {battery}%")
        
        # Scenario tracking
        if 'scenario' in sensor_data:
            processed_data['scenario'] = sensor_data['scenario']
            print(f"🎯 Scenario: {sensor_data['scenario']}")
        
        # Create comprehensive status
        alerts = []
        if processed_data.get('temperature_alert'):
            alerts.append(processed_data['temperature_alert'])
        if processed_data.get('humidity_alert'):
            alerts.append(processed_data['humidity_alert'])
        if processed_data.get('obstacle_alert'):
            alerts.append(processed_data['obstacle_alert'])
        if processed_data.get('lighting_alert'):
            alerts.append(processed_data['lighting_alert'])
        if processed_data.get('battery_alert'):
            alerts.append(processed_data['battery_alert'])
        
        processed_data['active_alerts'] = alerts
        processed_data['alert_count'] = len(alerts)
        
        if len(alerts) > 0:
            processed_data['overall_status'] = 'ALERT'
            print(f"🚨 SYSTEM ALERTS: {', '.join(alerts)}")
        else:
            processed_data['overall_status'] = 'NORMAL'
            print("✅ All systems normal")
        
        # Store in DynamoDB for historical analysis
        try:
            # Convert float values to Decimal for DynamoDB
            dynamodb_item = json.loads(json.dumps(processed_data), parse_float=Decimal)
            
            # Add partition key (robot_id) and sort key (timestamp)
            dynamodb_item['id'] = f"{robot_id}#{timestamp}"
            
            table.put_item(Item=dynamodb_item)
            print(f"💾 Data stored in DynamoDB: {robot_id}")
            
        except Exception as db_error:
            print(f"⚠️ DynamoDB error (continuing anyway): {str(db_error)}")
        
        # Calculate some real-time analytics
        analytics = {
            'data_points_processed': 1,
            'timestamp': timestamp,
            'robot_health_score': calculate_health_score(processed_data)
        }
        
        print(f"📊 Robot Health Score: {analytics['robot_health_score']}/100")
        print(f"✅ Processing complete for robot {robot_id}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Robot data processed and stored successfully',
                'robot_id': robot_id,
                'processed_data': processed_data,
                'analytics': analytics
            }, default=str)
        }
        
    except Exception as e:
        print(f"❌ Error processing robot data: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Error processing robot data',
                'error': str(e)
            })
        }

def calculate_health_score(data):
    """Calculate overall robot health score (0-100)"""
    score = 100
    
    # Battery impact
    if 'battery_level' in data:
        battery = data['battery_level']
        if battery < 20:
            score -= 30
        elif battery < 40:
            score -= 15
    
    # Alert impact
    alert_count = data.get('alert_count', 0)
    score -= (alert_count * 10)
    
    # Risk level impact
    risk = data.get('risk_level', 'LOW')
    if risk == 'HIGH':
        score -= 20
    elif risk == 'MEDIUM':
        score -= 10
    
    return max(0, score)

