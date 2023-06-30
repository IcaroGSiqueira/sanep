import paho.mqtt.client as mqtt
import json
import time
import random
import uuid

# MQTT broker configuration
mqtt_broker = "mqtt.example.com"
mqtt_port = 1883
mqtt_topic = "sensors/data"

# Sensor types and their respective ranges
sensor_types = {
    "temperature": (3, 37),
    "humidity": (10, 95),
    "conductivity": (200, 1500), 
    "ph": (7, 9),
    "pressure": (50, 2000),
}

# Time interval between sensor data updates (in seconds)
update_interval = 60

# Create MQTT client
client = mqtt.Client()

# Connect to MQTT broker
client.connect(mqtt_broker, mqtt_port)

# Dictionary of repositories with their UUIDs
repositories = {
    "Repository A": str(uuid.uuid4()),
    "Repository B": str(uuid.uuid4()),
    "Repository C": str(uuid.uuid4()),
}

# Dictionary of gateway names with their UUIDs
gateway_names = {
    "Gateway 1": str(uuid.uuid4()),
    "Gateway 2": str(uuid.uuid4()),
    "Gateway 3": str(uuid.uuid4()),
}

# Dictionary of sensor names with their UUIDs
sensor_names = {
    "Sensor 1": str(uuid.uuid4()),
    "Sensor 2": str(uuid.uuid4()),
    "Sensor 3": str(uuid.uuid4()),
}

def generate_fake_data(sensor_type, min_value, max_value):
    """
    Generate fake sensor data within the specified range for a given sensor type.
    """
    if sensor_type == "temperature":
        return round(random.uniform(min_value, max_value), 2)
    elif sensor_type == "humidity":
        return round(random.uniform(min_value, max_value), 1)
    elif sensor_type == "conductivity":
        return round(random.uniform(min_value, max_value), 2)
    elif sensor_type == "ph":
        return round(random.uniform(min_value, max_value), 2)
    elif sensor_type == "pressure":
        return round(random.uniform(min_value, max_value), 2)
    else:
        return None


def publish_fake_data():
    """
    Publish fake sensor data to the MQTT channel.
    """
    for sensor_type, value_range in sensor_types.items():
        min_value, max_value = value_range
        fake_data = generate_fake_data(sensor_type, min_value, max_value)

        if fake_data is not None:
            repository_name = random.choice(list(repositories.keys()))
            repository_uuid = repositories[repository_name]

            gateway_name = random.choice(list(gateway_names.keys()))
            gateway_uuid = gateway_names[gateway_name]
            gateway_model = "Gateway Model"
            gateway_status = random.choice([True, False])

            sensor_name = random.choice(list(sensor_names.keys()))
            sensor_uuid = sensor_names[sensor_name]
            sensor_model = "Sensor Model"
            sensor_description = "Sensor Description"
            sensor_status = random.choice([True, False])

            data = {
                "Repository": repository_uuid,
                "RepositoryDescription": "Your Repository Description",
                "Gateway": gateway_uuid,
                "GatewayName": gateway_name,
                "GatewayModel": gateway_model,
                "GatewayStatus": gateway_status,
                "Sensor": sensor_uuid,
                "SensorName": sensor_name,
                "SensorModel": sensor_model,
                "SensorDescription": sensor_description,
                "SensorStatus": sensor_status,
                "SensorType": sensor_type,
                "SensorData": fake_data,
                "SensorDataDatetime": str(datetime.datetime.now()),
            }

            message = json.dumps(data)

            # Publish the message to the MQTT channel
            client.publish(mqtt_topic, message)

    print("Fake data published.")


# Infinite loop to continuously publish fake sensor data
while True:
    publish_fake_data()
    time.sleep(update_interval)

# Disconnect from MQTT broker
client.disconnect()
