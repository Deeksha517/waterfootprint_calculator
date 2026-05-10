import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "waterfootprint.db")

def setup():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Create the users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()
    print("✅ Users table successfully added to waterfootprint.db!")

if __name__ == "__main__":
    setup()