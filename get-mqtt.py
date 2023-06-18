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
    try:
        repository_name = data.get('Repository')
        repository_description = data.get('RepositoryDescription')

        gateway_uuid = data.get('Gateway')
        gateway_name = data.get('GatewayName')
        gateway_model = data.get('GatewayModel')
        gateway_status = data.get('GatewayStatus')

        sensor_uuid = data.get('Sensor')
        sensor_name = data.get('SensorName')
        sensor_model = data.get('SensorModel')
        sensor_description = data.get('SensorDescription')
        sensor_status = data.get('SensorStatus')
        sensor_type = data.get('SensorType')

        raw_data = data.get('SensorData')
        sensor_datetime = data.get('SensorDataDatetime')

        sensor_data = round(float(raw_data), 1) if raw_data is not None else None

        created_at = datetime.datetime.now()
        created_at_utc = datetime.datetime.now(pytz.timezone('UTC'))

        return {
            'repository': {
                'name': repository_name,
                'description': repository_description
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
                'date_time': sensor_datetime,
            },
            'created_at': created_at,
            'created_at_utc': created_at_utc,
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
        repository_name = data['repository']['name']
        db_cursor.execute("SELECT id FROM repositories WHERE name = %s", (repository_name,))
        repository_result = db_cursor.fetchone()

        if repository_result is None:
            # Repositório não existe, insere novo repositório
            db_cursor.execute("INSERT INTO repositories (name, created_at, updated_at) VALUES (%s, %s, %s)",
                              (repository_name, data['created_at'], data['created_at']))
            db_conn.commit()
            repository_id = db_cursor.lastrowid
        else:
            repository_id = repository_result[0]

        # Verifica se o gateway existe
        gateway_uuid = data['gateway']['uuid']
        db_cursor.execute("SELECT id FROM gateways WHERE id = %s", (gateway_uuid,))
        gateway_result = db_cursor.fetchone()

        if gateway_result is None:
            # Gateway não existe, insere novo gateway
            gateway_name = data['gateway']['name']
            gateway_model = data['gateway']['model']
            gateway_status = data['gateway']['status']
            db_cursor.execute("INSERT INTO gateways (id, repository_id, name, model, status, created_at, updated_at) "
                              "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                              (gateway_uuid, repository_id, gateway_name, gateway_model, gateway_status,
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
            db_cursor.execute("INSERT INTO sensors (id, gateway_uuid, type_id, name, model, description, status, "
                              "created_at, updated_at) "
                              "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                              (sensor_uuid, gateway_uuid, sensor_type, sensor_name, sensor_model,
                               sensor_description, sensor_status, data['created_at'],
                               data['created_at']))
            db_conn.commit()

        # Insere os dados do sensor
        db_cursor.execute("INSERT INTO sensor_data (sensor_id, data, created_at_utc, created_at) "
                          "VALUES (%s, %s, %s, %s)",
                          (sensor_uuid, data['sensor_data']['data'], data['created_at_utc'],
                           data['created_at']))
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
