import paho.mqtt.client as mqtt
import json
import time
from datetime import datetime, timezone
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

# Retorno quando um cliente recebe um CONNACK do Broker, confirmando a subscricao
def on_connect(client, userdata, flags, rc):
    print("Conectado, com o seguinte retorno do Broker: "+str(rc))

    # O subscribe fica no on_connect pois, caso perca a conexao ele a renova
    # Lembrando que quando usado o #, voce estah especificando que tudo que 
    # chegar apos a barra do topico, sera recebido
    client.subscribe("pi-iv-a/dados")

# Callback responsavel por receber uma mensagem publicada no topico acima
def on_message(client, userdata, msg):
    # print(msg.topic+" "+str(msg.payload))

    try:
        m_decode=str(msg.payload.decode("utf-8","ignore"))
        dados_python = json.loads(m_decode)

        value = float(dados_python['Valor'])
        value_rounded = round(value,1)
        date_time = str(dados_python['DataHora'])
        description = str(dados_python['Descricao'])
        origin = str(dados_python['Origem'])
        created_at = datetime.datetime.now()
        created_at_utc = datetime.datetime.now(pytz.timezone('UTC'))

        # data_e_hora_em_texto = data_e_hora_atuais.strftime("%d/%m/%Y %H:%M:%S")

        # print ("Valor Sensor: " + str(valor))
        # print ("Data e Hora: " + datahora)
        # print ("Descricao: " + description)
        # print ("Origem: " + origin + "\n")
        # print ("Data e Hora em Texto: " + data_e_hora_em_texto)

        db_cursor = db_conn.cursor()
        sql = "INSERT INTO posts (value, datetime, description, origin, created_at_utc, created_at) VALUES (%s, %s, %s, %s, %s, %s)"
        val = (value_rounded, date_time, description, origin, created_at_utc, created_at)
        db_cursor.execute(sql, val)
        db_conn.commit()

    except Exception as err:
        print("Erro na leitura do JSON via Broker MQTT ou Gravacao Banco. ERRO: ", err)

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

# Define um usuario e senha para o Broker, se nao tem, nao use esta linha
#client.username_pw_set("Xxxxx", password="ZZZZzzz")

# Conecta no MQTT Broker
client.connect("broker.hivemq.com", 1883)

# Inicia o loop
client.loop_forever()