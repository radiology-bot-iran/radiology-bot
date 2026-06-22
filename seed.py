from database import conn, cursor

cursor.execute(
    "INSERT INTO events (title, date, capacity) VALUES (?, ?, ?)",
    ("Seminar - Radiology Updates", "2026-07-10", 100)
)

conn.commit()

print("Seed data inserted ✔")
