import mysql.connector
from mysql.connector import Error

DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "root",
    "password": "mysql@123",
    "database": "bike_rental",
    "autocommit": False
}

def get_db_connection():
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        print(f"\n[DATABASE CONNECTION ERROR]: {e}\n")
        return None