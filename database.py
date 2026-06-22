import sqlite3

# دیتابیس اصلی پروژه
conn = sqlite3.connect("bot.db", check_same_thread=False)
cursor = conn.cursor()

# ---------------- USERS TABLE ----------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    name TEXT
)
""")

# ---------------- EVENTS TABLE ----------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    date TEXT,
    capacity INTEGER
)
""")

# ---------------- REGISTRATIONS TABLE ----------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS registrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    event_id INTEGER
)
""")

conn.commit()

print("Database initialized ✔")