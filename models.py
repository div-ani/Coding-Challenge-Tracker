import sqlite3
from config import Config

def get_db():
    """
    Connects to the SQLite database and returns a connection object.
    row_factory is set to sqlite3.Row so we can access columns by name.
    """
    conn = sqlite3.connect(Config.DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """
    Creates necessary tables if they do not exist yet.
    """
    conn = get_db()
    cursor = conn.cursor()

    # Table for storing email reminder subscriptions
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            event_id TEXT NOT NULL,
            event_name TEXT NOT NULL,
            reminder_time TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Table for storing user settings and interests
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            handle TEXT UNIQUE NOT NULL,
            rating INTEGER DEFAULT 0,
            interests TEXT DEFAULT '',
            level TEXT DEFAULT 'Beginner',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()

def save_reminder(email, event_id, event_name, reminder_time):
    """
    Saves a new reminder request into the database.
    """
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO reminders (email, event_id, event_name, reminder_time)
        VALUES (?, ?, ?, ?)
    ''', (email, event_id, event_name, reminder_time))
    conn.commit()
    conn.close()

def get_all_reminders():
    """
    Fetches all registered reminders from the database.
    """
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM reminders ORDER BY created_at DESC')
    rows = cursor.fetchall()
    conn.close()
    return rows

def save_user_profile(handle, rating, interests, level):
    """
    Saves or updates user profile information in SQLite.
    """
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO user_profiles (handle, rating, interests, level, updated_at)
        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(handle) DO UPDATE SET
            rating = excluded.rating,
            interests = excluded.interests,
            level = excluded.level,
            updated_at = CURRENT_TIMESTAMP
    ''', (handle.strip(), rating, interests.strip(), level.strip()))
    conn.commit()
    conn.close()

def get_user_profile(handle):
    """
    Retrieves user profile details for a given Codeforces handle.
    """
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM user_profiles WHERE LOWER(handle) = LOWER(?)', (handle.strip(),))
    row = cursor.fetchone()
    conn.close()
    return row
