import os
import time
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error

load_dotenv()

def get_connection():
    for i in range(10):
        try:
            conn = mysql.connector.connect(
                host=os.getenv("DB_HOST"),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"),
                database=os.getenv("DB_NAME")
            )
            if conn.is_connected():
                return conn
        except Error as e:
            print(f"Attempt {i+1}/10 failed: {e}")
            time.sleep(3)
    raise Exception("Failed to connect to MySQL after multiple attempts.")
