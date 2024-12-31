import sqlite3

DB_FILE = 'bookings.db'

def check_columns():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('PRAGMA table_info(bookings)')
    columns = cursor.fetchall()
    conn.close()
    return columns

columns = check_columns()
print("bookings 表的列:")
for column in columns:
    print(column)