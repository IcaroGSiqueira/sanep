import paho.mqtt.client as mqtt
import json
import datetime
import mysql.connector
import pytz
import os
from dotenv import load_dotenv

load_dotenv()

host = os.getenv("MYSQL_HOST")
usr = os.getenv("MYSQL_USER")
passw = os.getenv("MYSQL_PASSWORD")
db = os.getenv("MYSQL_DB_NAME")

db_conn = mysql.connector.connect(host=host, user=usr, password=passw, database=db)

mqtt_topic = os.getenv("MQTT_TOPIC")
mqtt_broker = os.getenv("MQTT_BROKER")
mqtt_port = int(os.getenv("MQTT_PORT"))
mqtt_secure = bool(os.getenv("MQTT_SECURE"))
mqtt_user = os.getenv("MQTT_USER")
mqtt_password = os.getenv("MQTT_PASSWORD")

def process_data(data):
    tank_name = None
    tank_description = None

    gateway_uuid = None
    gateway_name = None
    gateway_status = None

    sensor_uuid = None
    sensor_data = None

    data_hora_formatada = None

    devices = []

    try:
        tank_name = 'Barragem'

        data_type = data.get('type')

        if data_type == 'publication':
            sensor_uuid = data.get('uuid')
            raw_data = data.get('data')

            sensor_data = round(float(raw_data), 1) if raw_data is not None else None

            data_datetime = data.get('gathered_at').split("T")
            time_datetime = data_datetime[1].split(".")
            data_hora_formatada = data_datetime[0] + " " + time_datetime[0]


        elif data_type == 'identification':
            gateway_uuid = data.get('gateway').get('uuid')
            gateway_name = data.get('gateway').get('name')
            gateway_status = data.get('gateway').get('status', True)

            devices = data.get('devices')

            data_datetime = data.get('gathered_at').split("T")
            time_datetime = data_datetime[1].split(".")
            data_hora_formatada = data_datetime[0] + " " + time_datetime[0]

        elif data_type == 'log':
            gateway_uuid = data.get('uuid_gateway')
            raw_data = data.get('data')

        created_at = datetime.datetime.now()

        return {
            'type': data_type,
            'tank': {
                'name': tank_name,
                'description': tank_description,
            },
            'gateway': {
                'uuid': gateway_uuid,
                'name': gateway_name,
                'status': gateway_status,
            },
            'devices': devices,
            'sensor_data': {
                'uuid': sensor_uuid,
                'data': sensor_data,
                'date_time': data_hora_formatada,
            },
            'created_at': created_at,
        }
    except Exception as err:
        print("Erro ao processar os dados:", err)
        return None

def insert_pub_data(data, db_cursor):
    # Verifica se o sensor existe
    sensor_uuid = data.get('sensor_data').get('uuid')
    db_cursor.execute("SELECT id FROM sensors WHERE id = %s", (sensor_uuid,))
    sensor_result = db_cursor.fetchone()
    created_at = data.get('created_at')

    if sensor_result is None:
        # Sensor não existe, insere novo sensor
        sensor_name = 'temporary_name_' + sensor_uuid
        db_cursor.execute("INSERT INTO sensors "
            "(id, name, created_at, updated_at) "
            "VALUES (%s, %s, %s, %s)",
            (
                sensor_uuid,
                sensor_name,
                created_at,
                created_at
                )
            )

        db_conn.commit()

    value = data.get('sensor_data').get('data')
    value_date = data.get('sensor_data').get('date_time')

    # Insere os dados do sensor
    db_cursor.execute("INSERT INTO sensor_data (sensor_id, data, created_at) "
                      "VALUES (%s, %s, %s)",
                      (
                        sensor_uuid,
                        value,
                        value_date
                        )
                      )
    db_conn.commit()

def insert_config_data(data, db_cursor):
    # Verifica se o gateway existe
    gateway_uuid = data.get('gateway').get('uuid')
    db_cursor.execute("SELECT id FROM gateways WHERE id = %s", (gateway_uuid,))
    gateway_result = db_cursor.fetchone()
    created_at = data.get('created_at')

    if gateway_result is None:
        # Gateway não existe, insere novo gateway
        gateway_name = data.get('gateway').get('name')
        gateway_status = data.get('gateway').get('status')
        tank_id = data.get('tank_id')

        db_cursor.execute("INSERT INTO gateways (id, tank_id, name, status, created_at, updated_at) "
                          "VALUES (%s, %s, %s, %s, %s, %s)",
                          (
                            gateway_uuid,
                            tank_id,
                            gateway_name,
                            gateway_status,
                            created_at,
                            created_at
                            )
                          )
        db_conn.commit()

    # Verifica se cada sensor existe

    for sensor in data['devices']:
        sensor_uuid = sensor.get('uuid')

        db_cursor.execute("SELECT id FROM sensors WHERE id = %s", (sensor_uuid,))
        sensor_result = db_cursor.fetchone()

        sensor_name = sensor.get('name')
        sensor_status = sensor.get('status')
        sensor_type = sensor.get('driver')

        sensor_types = {
            'temperature': 1,
            'humidity': 2,
            'conductivity': 3,
            'ph': 4,
            'pressure': 5,
            'wind': 6,
        }

        type_id = sensor_types.get(sensor_type, None)

        if sensor_result is None and type_id is not None:
            # Sensor não existe, insere novo sensor

            db_cursor.execute("INSERT INTO sensors "
                "(id, gateway_id, type_id, name, status, created_at, updated_at) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (
                    sensor_uuid,
                    gateway_uuid,
                    type_id,
                    sensor_name,
                    sensor_status,
                    created_at,
                    created_at
                    )
                )

            db_conn.commit()
        elif type_id is not None:
            # Sensor existe, atualiza os seus dados
            db_cursor.execute("UPDATE sensors SET "
                "gateway_id = %s, "
                "type_id = %s, "
                "name = %s, "
                "status = %s, "
                "created_at = %s, "
                "updated_at = %s "
                "WHERE id = %s",
                (
                    gateway_uuid,
                    type_id,
                    sensor_name,
                    sensor_status,
                    created_at,
                    created_at,
                    sensor_uuid
                    )
                )

            db_conn.commit()

def insert_data_into_database(data):
    if data is None:
        return

    db_cursor = db_conn.cursor()

    try:
        # Verifica se o repositório existe
        tank_name = data.get('tank').get('name')
        db_cursor.execute("SELECT id FROM tanks WHERE name = %s", (tank_name,))
        tank_result = db_cursor.fetchone()

        if tank_result is None:
            # Repositório não existe, insere novo repositório
            created_at = data.get('created_at')
            db_cursor.execute("INSERT INTO tanks (name, created_at, updated_at) VALUES (%s, %s, %s)",
                              (tank_name, created_at, created_at))
            db_conn.commit()
            data['tank_id'] = db_cursor.lastrowid
        else:
            data['tank_id'] = tank_result[0]

        data_type = data.get('type')

        if data_type == 'identification':
            insert_config_data(data, db_cursor)

        elif data_type == 'publication':
            insert_pub_data(data, db_cursor)

    except Exception as err:
        print("Erro ao inserir os dados no banco de dados:", err)

    db_cursor.close()


# Retorno quando um cliente recebe um CONNACK do Broker, confirmando a subscricao
def on_connect(client, userdata, flags, rc):
    print("Conectado, com o seguinte retorno do Broker: " + str(rc))

    # O subscribe fica no on_connect pois, caso perca a conexao ele a renova
    # Lembrando que quando usado o #, voce estah especificando que tudo que
    # chegar apos a barra do topico, sera recebido
    client.subscribe(mqtt_topic)


# Callback responsavel por receber uma mensagem publicada no topico acima
def on_message(client, userdata, msg):
    print(msg.topic+" "+str(msg.payload))
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

# Conecta no MQTT Broker
client.connect(mqtt_broker, mqtt_port)

# Inicia o loop
client.loop_forever()
