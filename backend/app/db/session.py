import sqlite3

def get_db():
    """Create database connection with Row factory and check_same_thread=False"""
    conn = sqlite3.connect('vulnerable_app.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize users table if it doesn't exist"""
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            email TEXT,
            password TEXT
        )
    ''')
    conn.commit()
    conn.close()