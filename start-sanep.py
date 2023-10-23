import paho.mqtt.client as mqtt
import json
import datetime
import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

host = os.getenv("MYSQL_HOST")
usr = os.getenv("MYSQL_USER")
passw = os.getenv("MYSQL_PASSWORD")
db = os.getenv("MYSQL_DB_NAME")

mqtt_topic = os.getenv("MQTT_TOPIC")
mqtt_broker = os.getenv("MQTT_BROKER")
mqtt_port = int(os.getenv("MQTT_PORT"))
mqtt_secure = bool(os.getenv("MQTT_SECURE"))
mqtt_user = os.getenv("MQTT_USER")
mqtt_password = os.getenv("MQTT_PASSWORD")


def process_data(data):
    gateway_uuid = None
    gateway_name = None

    sensor_uuid = None
    sensor_data = None

    message = None

    data_hora_formatada = None

    devices = []

    try:
        data_type = data.get("type", None)

        if data_type == "publication":
            sensor_uuid = data.get("uuid")
            raw_data = data.get("data")

            sensor_data = round(float(raw_data), 1) if raw_data is not None else None

            data_datetime = data.get("gathered_at").split("T")
            time_datetime = data_datetime[1].split(".")
            data_hora_formatada = data_datetime[0] + " " + time_datetime[0]

        elif data_type == "identification":
            gateway_uuid = data.get("gateway").get("uuid")
            gateway_name = data.get("gateway").get("name")

            devices = data.get("devices")

            data_datetime = data.get("gathered_at").split("T")
            time_datetime = data_datetime[1].split(".")
            data_hora_formatada = data_datetime[0] + " " + time_datetime[0]

        elif data_type == "log":
            gateway_uuid = data.get("gateway").get("uuid")
            message = data.get("data")

            data_datetime = data.get("gathered_at").split("T")
            time_datetime = data_datetime[1].split(".")
            data_hora_formatada = data_datetime[0] + " " + time_datetime[0]

        created_at = datetime.datetime.now()

        return {
            "type": data_type,
            "gateway": {
                "uuid": gateway_uuid,
                "name": gateway_name,
            },
            "devices": devices,
            "sensor_data": {
                "uuid": sensor_uuid,
                "data": sensor_data,
                "date_time": data_hora_formatada,
            },
            "log": {
                "message": message,
                "date_time": data_hora_formatada,
            },
            "created_at": created_at,
        }
    except Exception as err:
        print("Erro ao processar os dados:", err)
        return None


def insert_pub_data(data, db_cursor):
    # Verifica se o sensor existe
    sensor_uuid = data.get("sensor_data").get("uuid")
    db_cursor.execute("SELECT id FROM sensors WHERE id = %s", (sensor_uuid,))
    sensor_result = db_cursor.fetchone()
    created_at = data.get("created_at")

    if sensor_result is None:
        # Sensor não existe, insere novo sensor
        sensor_name = "temporary_name_" + sensor_uuid
        db_cursor.execute(
            "INSERT INTO sensors "
            "(id, name, created_at, updated_at) "
            "VALUES (%s, %s, %s, %s)",
            (sensor_uuid, sensor_name, created_at, created_at),
        )

        db_conn.commit()

    value = data.get("sensor_data").get("data")
    value_date = data.get("sensor_data").get("date_time")

    # Insere os dados do sensor
    db_cursor.execute(
        "INSERT INTO sensor_data (sensor_id, data, gathered_at, created_at) "
        "VALUES (%s, %s, %s, %s)",
        (sensor_uuid, value, value_date, created_at),
    )
    db_conn.commit()


def insert_config_data(data, db_cursor):
    # Verifica se o gateway existe
    gateway_uuid = data.get("gateway").get("uuid")
    db_cursor.execute("SELECT id FROM gateways WHERE id = %s", (gateway_uuid,))
    gateway_result = db_cursor.fetchone()
    created_at = data.get("created_at")

    if gateway_result is None:
        # Gateway não existe, insere novo gateway
        gateway_name = data.get("gateway").get("name")

        db_cursor.execute(
            "INSERT INTO gateways (id, name, created_at, updated_at) "
            "VALUES (%s, %s, %s, %s)",
            (
                gateway_uuid,
                gateway_name,
                created_at,
                created_at,
            ),
        )
        db_conn.commit()

    # Verifica se cada sensor existe

    for sensor in data["devices"]:
        sensor_uuid = sensor.get("uuid")

        db_cursor.execute("SELECT id FROM sensors WHERE id = %s", (sensor_uuid,))
        sensor_result = db_cursor.fetchone()

        sensor_name = sensor.get("name")
        sensor_type = sensor.get("driver")

        sensor_types = {
            "temperature": 1,
            "humidity": 2,
            "conductivity": 3,
            "ph": 4,
            "pressure": 5,
            "wind": 6,
        }

        type_id = sensor_types.get(sensor_type, None)

        if sensor_result is None and type_id is not None:
            # Sensor não existe, insere novo sensor

            db_cursor.execute(
                "INSERT INTO sensors "
                "(id, gateway_id, type_id, name, created_at, updated_at) "
                "VALUES (%s, %s, %s, %s, %s, %s)",
                (
                    sensor_uuid,
                    gateway_uuid,
                    type_id,
                    sensor_name,
                    created_at,
                    created_at,
                ),
            )

            db_conn.commit()
        elif type_id is not None:
            # Sensor existe, atualiza os seus dados
            db_cursor.execute(
                "UPDATE sensors SET "
                "gateway_id = %s, "
                "type_id = %s, "
                "name = %s, "
                "created_at = %s, "
                "updated_at = %s "
                "WHERE id = %s",
                (
                    gateway_uuid,
                    type_id,
                    sensor_name,
                    created_at,
                    created_at,
                    sensor_uuid,
                ),
            )

            db_conn.commit()


def insert_log_data(data, db_cursor):
    # Verifica se o gateway existe
    gateway_uuid = data.get("gateway").get("uuid")
    db_cursor.execute("SELECT id FROM gateways WHERE id = %s", (gateway_uuid,))
    gateway_result = db_cursor.fetchone()

    if gateway_result is None:
        # Gateway não existe, insere novo gateway
        gateway_name = "temporary_name_" + gateway_uuid
        created_at = data.get("created_at")

        db_cursor.execute(
            "INSERT INTO gateways (id, name, created_at, updated_at) "
            "VALUES (%s, %s, %s, %s)",
            (
                gateway_uuid,
                gateway_name,
                created_at,
                created_at,
            ),
        )
        db_conn.commit()

    message = data.get("log").get("message")
    value_date = data.get("log").get("date_time")

    # Insere os dados do log
    db_cursor.execute(
        "INSERT INTO logs (gateway_uuid, message, created_at) " "VALUES (%s, %s, %s)",
        (gateway_uuid, message, value_date),
    )
    db_conn.commit()


def insert_data_into_database(data):
    if data is None:
        return
    try:
        db_conn = mysql.connector.connect(
            host=host, user=usr, password=passw, database=db
        )
        db_cursor = db_conn.cursor()

        data_type = data.get("type")

        if data_type == "identification":
            insert_config_data(data, db_cursor)

        elif data_type == "publication":
            insert_pub_data(data, db_cursor)

        elif data_type == "log":
            insert_log_data(data, db_cursor)

    except Exception as err:
        print("Erro ao inserir os dados no banco de dados:", err)

    finally:
        db_cursor.close()
        db_conn.close()


def on_connect(client, userdata, flags, rc):
    print("Conectado, com o seguinte retorno do Broker: " + str(rc))
    client.subscribe(mqtt_topic)


def on_message(client, userdata, msg):
    print(msg.topic + " " + str(msg.payload))
    try:
        m_decode = str(msg.payload.decode("utf-8", "ignore"))
        data = json.loads(m_decode)
        processed_data = process_data(data)
        if processed_data:
            insert_data_into_database(processed_data)
    except Exception as err:
        print("Erro ao receber ou processar a mensagem MQTT:", err)


client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message


if mqtt_secure:
    client.username_pw_set(mqtt_user, password=mqtt_password)

client.connect(mqtt_broker, mqtt_port)

client.loop_forever()
