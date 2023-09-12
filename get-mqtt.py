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
    gateway_model = None
    gateway_status = None

    sensor_uuid = None
    sensor_name = None
    sensor_model = None
    sensor_description = None
    sensor_status = None
    sensor_type = None

    try:
        tank_name = 'Reservatório R1'

        data_type = data.get('type')

        if data_type == 'collect':
            sensor_uuid = data.get('uuid_sensor')
            raw_data = data.get('data')

        elif data_type == 'configuration':
            gateway_uuid = data['gateway']['uuid']
            gateway_name = data['gateway']['name']
            gateway_status = True

            sensor_uuid = data['sensors']['uuid']
            sensor_name = data['sensors']['name']
            sensor_description = data['sensors']['description']
            sensor_status = True if data['sensors']['status'] == 'true' else False
            sensor_type = data['sensors']['type']

        elif data_type == 'log':
            gateway_uuid = data.get('uuid_gateway')
            raw_data = data.get('data')

        data_datetime = data.get('date')

        sensor_data = round(float(raw_data), 1) if raw_data is not None else None

        created_at = datetime.datetime.now()

        return {
            'type': data_type,
            'tank': {
                'name': tank_name,
                'description': tank_description
            },
            'gateway': {
                'uuid': gateway_uuid,
                'name': gateway_name,
                'model': gateway_model,
                'status': gateway_status
            },
            'sensor': {
                'uuid': sensor_uuid,
                'name': sensor_name,
                'model': sensor_model,
                'description': sensor_description,
                'status': sensor_status,
                'type': sensor_type
            },
            'sensor_data': {
                'data': sensor_data,
                'date_time': data_datetime,
            },
            'created_at': created_at,
        }
    except Exception as err:
        print("Erro ao processar os dados:", err)
        return None

def insert_data_into_database(data):
    if data is None:
        return

    db_cursor = db_conn.cursor()

    try:
        # Verifica se o repositório existe
        tank_name = data['tank']['name']
        db_cursor.execute("SELECT id FROM tanks WHERE name = %s", (tank_name,))
        tank_result = db_cursor.fetchone()

        if tank_result is None:
            # Repositório não existe, insere novo repositório
            db_cursor.execute("INSERT INTO tanks (name, created_at, updated_at) VALUES (%s, %s, %s)",
                              (tank_name, data['created_at'], data['created_at']))
            db_conn.commit()
            tank_id = db_cursor.lastrowid
        else:
            tank_id = tank_result[0]


        print(data)

        # Verifica o tipo de coleta
        data_type = data['type']
        if data_type == 'configuration':
            # Verifica se o gateway existe
            gateway_uuid = data['gateway']['uuid']
            db_cursor.execute("SELECT id FROM gateways WHERE id = %s", (gateway_uuid,))
            gateway_result = db_cursor.fetchone()

            if gateway_result is None:
                # Gateway não existe, insere novo gateway
                gateway_name = data['gateway']['name']
                gateway_model = data['gateway']['model']
                gateway_status = data['gateway']['status']
                db_cursor.execute("INSERT INTO gateways (id, tank_id, name, model, status, created_at, updated_at) "
                                  "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                                  (gateway_uuid, tank_id, gateway_name, gateway_model, gateway_status,
                                   data['created_at'], data['created_at']))
                db_conn.commit()

            # Verifica se o sensor existe
            sensor_uuid = data['sensor']['uuid']
            db_cursor.execute("SELECT id FROM sensors WHERE id = %s", (sensor_uuid,))
            sensor_result = db_cursor.fetchone()

            if sensor_result is None:
                # Sensor não existe, insere novo sensor
                sensor_name = data['sensor']['name']
                sensor_model = data['sensor']['model']
                sensor_description = data['sensor']['description']
                sensor_status = data['sensor']['status']
                sensor_type = data['sensor']['type']
                db_cursor.execute("INSERT INTO sensors (id, gateway_id, type_id, name, model, description, status, "
                                  "created_at, updated_at) "
                                  "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                                  (sensor_uuid, gateway_uuid, sensor_type, sensor_name, sensor_model,
                                   sensor_description, sensor_status, data['created_at'],
                                   data['created_at']))
                db_conn.commit()
            else:
                # Sensor existe, atualiza os seus dados
                sensor_name = data['sensor']['name']
                sensor_model = data['sensor']['model']
                sensor_description = data['sensor']['description']
                sensor_status = data['sensor']['status']
                sensor_type = data['sensor']['type']
                db_cursor.execute("UPDATE sensors SET "
                                    "gateway_id = %s, "
                                    "type_id = %s, "
                                    "name = %s, "
                                    "model = %s, "
                                    "description = %s, "
                                    "status = %s, "
                                    "created_at = %s, "
                                    "updated_at = %s "
                                    "WHERE id = %s",
                                  (gateway_uuid, sensor_type, sensor_name, sensor_model,
                                   sensor_description, sensor_status, data['created_at'],
                                   data['created_at'], sensor_uuid))
                db_conn.commit()

        elif data_type == 'collect':
            # Verifica se o sensor existe
            sensor_uuid = data['sensor']['uuid']
            db_cursor.execute("SELECT id FROM sensors WHERE id = %s", (sensor_uuid,))
            sensor_result = db_cursor.fetchone()

            if sensor_result is None:
                # Sensor não existe, insere novo sensor
                sensor_name = data['sensor']['name']
                sensor_model = data['sensor']['model']
                sensor_description = data['sensor']['description']
                sensor_status = data['sensor']['status']
                sensor_type = data['sensor']['type']
                db_cursor.execute("INSERT INTO sensors (id, type_id, name, model, description, status, "
                                  "created_at, updated_at) "
                                  "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                                  (sensor_uuid, sensor_type, sensor_name, sensor_model,
                                   sensor_description, sensor_status, data['created_at'],
                                   data['created_at']))
                db_conn.commit()

            # Insere os dados do sensor
            db_cursor.execute("INSERT INTO sensor_data (sensor_id, data, created_at) "
                              "VALUES (%s, %s, %s)",
                              (sensor_uuid, data['sensor_data']['data']))
            db_conn.commit()

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
