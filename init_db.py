import sqlite3
import hashlib

DB_FILE = 'bookings.db'

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # 创建用户表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        feishu_webhook TEXT,
        notification_method TEXT DEFAULT 'none'
    )
    ''')
    # 创建预约表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        cookie TEXT NOT NULL,
        seat_id TEXT NOT NULL,
        date TEXT NOT NULL,
        time_slots TEXT NOT NULL,
        processed BOOLEAN NOT NULL,
        result TEXT,
        loop_booking BOOLEAN DEFAULT FALSE,
        frequency INTEGER DEFAULT 10,
        last_result TEXT,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    conn.commit()
    conn.close()

init_db()