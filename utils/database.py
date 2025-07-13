import sqlite3
import uuid
from datetime import datetime
import logging

DATABASE_NAME = 'chat_history.db'
CONFIG_DATABASE_NAME = 'config.db'

logger = logging.getLogger(__name__)

def get_db_connection():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def get_config_db_connection():
    conn = sqlite3.connect(CONFIG_DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    conn = get_db_connection()
    cursor = conn.cursor()

    # 创建用户表，存储用户名和密码
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            user_id TEXT, 
            title TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            message_id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL, -- 'user' or 'assistant'
            content TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions (session_id)
        )
    ''')
    conn.commit()
    conn.close()
    config_conn = get_config_db_connection()
    config_cursor = config_conn.cursor()
    config_cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT,
            description TEXT
        )
    ''')
    config_conn.commit()
    config_conn.close()

# 用户注册
def register_user(user_id, password):
    if user_exists(user_id):
        return False
        
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (user_id, password) VALUES (?, ?)",
            (user_id, password)
        )
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Database error during user registration: {e}")
        return False
    finally:
        conn.close()

# 验证用户登录
def verify_user(user_id, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # 先检查用户是否存在
        cursor.execute(
            "SELECT 1 FROM users WHERE user_id = ?",
            (user_id,)
        )
        user_exists = cursor.fetchone() is not None
        
        if not user_exists:
            print(f"User {user_id} does not exist")
            return False
            
        # 验证密码
        cursor.execute(
            "SELECT password FROM users WHERE user_id = ?",
            (user_id,)
        )
        user = cursor.fetchone()
        
        if user and user['password'] == password:
            print(f"User {user_id} login successful")
            return True
            
        print(f"Password incorrect for user {user_id}")
        return False
    except sqlite3.Error as e:
        print(f"Database error during user verification: {e}")
        return False
    finally:
        conn.close()

# 检查用户是否存在
def user_exists(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT 1 FROM users WHERE user_id = ?",
            (user_id,)
        )
        result = cursor.fetchone() is not None
        print(f"Checking if user {user_id} exists: {result}")
        return result
    except sqlite3.Error as e:
        print(f"Database error checking if user exists: {e}")
        return False
    finally:
        conn.close()

def create_session(user_id=None, title='New Chat'):
    session_id = str(uuid.uuid4())
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO sessions (session_id, user_id, title) VALUES (?, ?, ?)",
            (session_id, user_id, title)
        )
        conn.commit()
        return session_id
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None
    finally:
        conn.close()

def add_message(session_id, role, content):
    message_id = str(uuid.uuid4())
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO messages (message_id, session_id, role, content) VALUES (?, ?, ?, ?)",
            (message_id, session_id, role, content)
        )
        conn.commit()
        return message_id
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None
    finally:
        conn.close()

def get_messages(session_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT role, content, timestamp FROM messages WHERE session_id = ? ORDER BY timestamp ASC",
            (session_id,)
        )
        messages = [{'role': row['role'], 'content': row['content'], 'timestamp': row['timestamp']} for row in cursor.fetchall()]
        return messages
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return []
    finally:
        conn.close()

def get_sessions(user_id=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        if user_id:
            cursor.execute(
                "SELECT session_id, title, created_at FROM sessions WHERE user_id = ? ORDER BY created_at DESC",
                (user_id,)
            )
        else:
            cursor.execute(
                "SELECT session_id, title, created_at FROM sessions ORDER BY created_at DESC"
            )
        sessions = [{'session_id': row['session_id'], 'title': row['title'], 'created_at': row['created_at']} for row in cursor.fetchall()]
        return sessions
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return []
    finally:
        conn.close()

def save_settings(settings: dict):
    """Saves a dictionary of settings to the config database."""
    conn = get_config_db_connection()
    cursor = conn.cursor()
    try:
        print(f"[DEBUG] Saving settings: {settings}")
        logger.debug(f"Saving settings: {settings}")
        for key, value in settings.items():
            cursor.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                (key, value)
            )
        conn.commit()
    except sqlite3.Error as e:
        print(f"Database error while saving settings: {e}")
    finally:
        conn.close()

def get_all_settings() -> dict:
    """Retrieves all settings from the config database as a dictionary."""
    conn = get_config_db_connection()
    cursor = conn.cursor()
    settings = {}
    try:
        cursor.execute("SELECT key, value FROM settings")
        rows = cursor.fetchall()
        for row in rows:
            settings[row['key']] = row['value']
        return settings
    except sqlite3.Error as e:
        print(f"Database error while getting all settings: {e}")
        return {}
    finally:
        conn.close()

def get_setting(key: str) -> str | None:
    """Retrieves a single setting value by its key from the config database."""
    conn = get_config_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        return row['value'] if row else None
    except sqlite3.Error as e:
        print(f"Database error while getting setting '{key}': {e}")
        return None
    finally:
        conn.close()

if __name__ == '__main__':
    create_tables()
    print("Database tables created successfully.")
