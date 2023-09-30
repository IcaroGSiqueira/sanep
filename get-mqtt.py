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

    devices = []

    try:
        tank_name = 'Barragem'

        sensor_uuid = data.get('uuid')
        raw_data = data.get('data')
        data_datetime = data.get('gathered_at')

        partes = data_datetime.split("T")

        segunda_parte = partes[1].split(".")

        data_hora_formatada = partes[0] + " " + segunda_parte[0]

        sensor_data = round(float(raw_data), 1) if raw_data is not None else None

        created_at = datetime.datetime.now()

        return {
            'tank': {
                'name': tank_name,
                'description': tank_description
            },
            'gateway': {
                'uuid': gateway_uuid,
                'name': gateway_name,
                'status': gateway_status
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

def insert_data_into_database(data):
    if data is None:
        return

    db_cursor = db_conn.cursor()

    try:
        # Verifica se o repositório existe
        tank_name = data['tank']['name']
        db_cursor.execute("SELECT id FROM tanks WHERE name = %s", (tank_name,))
        tank_result = db_cursor.fetchone()

        created_at = data['created_at']

        if tank_result is None:
            # Repositório não existe, insere novo repositório
            db_cursor.execute("INSERT INTO tanks (name, created_at, updated_at) VALUES (%s, %s, %s)",
                              (tank_name, created_at, created_at))
            db_conn.commit()
            tank_id = db_cursor.lastrowid
        else:
            tank_id = tank_result[0]

        # Verifica se o sensor existe
        sensor_uuid = data['sensor_data']['uuid']
        db_cursor.execute("SELECT id FROM sensors WHERE id = %s", (sensor_uuid,))
        sensor_result = db_cursor.fetchone()

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

        value = data['sensor_data']['data']
        value_date = data['sensor_data']['date_time']

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
