import os
import sys
import mysql.connector
from mysql.connector import Error

DB_NAME = "bike_rental"
DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "root",
    "password": "mysql@123",
    "autocommit": False
}

def load_queries():
    """Parses queries.sql and maps query names to SQL statements."""
    queries = {}
    path = os.path.join(os.path.dirname(__file__), "queries.sql")
    if not os.path.exists(path):
        return queries

    with open(path, "r", encoding="utf-8") as f:
        current_name = None
        current_sql = []
        for line in f:
            stripped = line.strip()
            if stripped.startswith("-- name:"):
                if current_name and current_sql:
                    queries[current_name] = " ".join(current_sql).rstrip(";").strip()
                current_name = stripped.replace("-- name:", "").strip()
                current_sql = []
            elif current_name and not stripped.startswith("--") and stripped:
                current_sql.append(stripped)
        if current_name and current_sql:
            queries[current_name] = " ".join(current_sql).rstrip(";").strip()

    return queries

# Global loaded queries dictionary
SQL = load_queries()

def load_schema(force_reset=False):
    """Executes schema.sql to initialize or reset database."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        if force_reset:
            cursor.execute(f"DROP DATABASE IF EXISTS {DB_NAME};")
            cursor.execute(f"CREATE DATABASE {DB_NAME};")
            conn.commit()
        else:
            cursor.execute("SHOW DATABASES LIKE %s", (DB_NAME,))
            if cursor.fetchone():
                cursor.close()
                conn.close()
                return
            cursor.execute(f"CREATE DATABASE {DB_NAME};")
            conn.commit()

        cursor.execute(f"USE {DB_NAME};")
        schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")

        if os.path.exists(schema_path):
            with open(schema_path, "r", encoding="utf-8") as f:
                sql_content = f.read()

            for raw_stmt in sql_content.split(";"):
                stmt = raw_stmt.strip()
                if stmt:
                    cursor.execute(stmt)
            conn.commit()
            print(f"[✓] Successfully loaded schema into '{DB_NAME}'!")
        cursor.close()
        conn.close()
    except Error as e:
        print(f"[SCHEMA LOAD ERROR]: {e}")

load_schema(force_reset=False)

def get_db_connection():
    try:
        return mysql.connector.connect(database=DB_NAME, **DB_CONFIG)
    except Error as e:
        if e.errno == 1049:
            load_schema(force_reset=False)
            try:
                return mysql.connector.connect(database=DB_NAME, **DB_CONFIG)
            except Error:
                pass
        print(f"[DATABASE CONNECTION ERROR]: {e}")
        return None

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--reset":
        load_schema(force_reset=True)
    else:
        conn = get_db_connection()
        print("CONNECTED TO MYSQL SUCCESSFULLY!" if conn else "CONNECTION FAILED")
        if conn:
            conn.close()