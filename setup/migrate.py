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

# Create the 'environments' table
db_cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS environments (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    )
"""
)


# Create the 'gateways' table
db_cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS gateways (
        id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
        environment_id INT,
        name VARCHAR(255),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        FOREIGN KEY (environment_id) REFERENCES environments (id) ON DELETE CASCADE
    )
"""
)

# Create the 'sensor_types' table
db_cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS sensor_types (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255),
        description TEXT,
        unit VARCHAR(50),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    )
"""
)

# Create the 'sensors' table
db_cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS sensors (
        id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
        gateway_id VARCHAR(36),
        type_id INT,
        name VARCHAR(255),
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        FOREIGN KEY (gateway_id) REFERENCES gateways (id) ON DELETE CASCADE,
        FOREIGN KEY (type_id) REFERENCES sensor_types (id) ON DELETE SET NULL
    )
"""
)

# Create the 'sensor_data' table
db_cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS sensor_data (
        id INT AUTO_INCREMENT PRIMARY KEY,
        sensor_id VARCHAR(36),
        data TEXT,
        gathered_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (sensor_id) REFERENCES sensors (id) ON DELETE CASCADE
    )
"""
)

# Create the 'rules' table
db_cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS rules (
        id INT AUTO_INCREMENT PRIMARY KEY,
        sensor_id VARCHAR(36),
        type_id INT,
        ´condition´ TINYTEXT,
        value VARCHAR(12),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        FOREIGN KEY (sensor_id) REFERENCES sensors (id) ON DELETE CASCADE,
        FOREIGN KEY (type_id) REFERENCES sensor_types (id) ON DELETE CASCADE
    )
"""
)

# Create the 'logs' table
db_cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS logs (
        id INT AUTO_INCREMENT PRIMARY KEY,
        gateway_id VARCHAR(36),
        message TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (gateway_id) REFERENCES gateways (id) ON DELETE CASCADE
    )
"""
)

# Create the 'telegram_users' table
db_cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS telegram_users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        code VARCHAR(16),
        active BOOLEAN DEFAULT True,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
"""
)


db_conn.commit()
db_conn.close()
