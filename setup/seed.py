import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

host = os.getenv("MYSQL_HOST")
usr = os.getenv("MYSQL_USER")
passw = os.getenv("MYSQL_PASSWORD")
db = os.getenv("MYSQL_DB_NAME")

db_conn = mysql.connector.connect(host=host, user=usr, password=passw, database=db)

db_cursor = db_conn.cursor()

# Check if sensor_types table already has data
db_cursor.execute("SELECT COUNT(*) FROM sensor_types")
result = db_cursor.fetchone()

if result[0] > 0:
    print("Sensor types already exist in the table. Skipping seeding.")
else:
    # Sensor type data
    sensor_types = [
        ("temperature", "Temperature", "°C"),
        ("humidity", "Air Humidity", "%"),
        ("conductivity", "Electric Conductivity", "uS/cm"),
        ("ph", "Water pH", "ph"),
        ("pressure", "Water Level", "m3"),
        ("wind", "Wind Velocity", "km/h"),
    ]

    # Add sensor types to the table
    for sensor_type in sensor_types:
        sql = "INSERT INTO sensor_types (name, description, unit) VALUES (%s, %s, %s)"
        db_cursor.execute(sql, sensor_type)

    db_conn.commit()

db_cursor.execute("SELECT COUNT(*) FROM environments")
result = db_cursor.fetchone()

if result[0] > 0:
    print("Environments already exist in the table. Skipping seeding.")
else:
    # Environments names
    environments_names = [f"Reservatório R{i}" for i in range(1, 25)]

    # Add environments to the table
    for environment_name in environments_names:
        sql = "INSERT INTO environments (name) VALUES (%s)"
        db_cursor.execute(sql, (environment_name,))

    db_conn.commit()

print("Seeding data completed.")
db_conn.close()
