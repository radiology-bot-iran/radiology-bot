from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

import sqlite3

# ---------------- DATABASE ----------------
conn = sqlite3.connect("bot.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    name TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    date TEXT,
    capacity INTEGER
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS registrations (
    user_id INTEGER,
    event_id INTEGER
)
""")

conn.commit()

# ---------------- CONFIG ----------------
TOKEN = "8723545702:AAFDjnjIj3-ZQ79X0y_5E4YHLtVXdqtA-SI"
ADMIN_ID = 8947941966

admin_state = {}
edit_state = {}

# ---------------- ADMIN CHECK ----------------
def is_admin(user_id: int):
    return user_id == ADMIN_ID


# ---------------- START ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user

    cursor.execute(
        "INSERT OR IGNORE INTO users (user_id, name) VALUES (?, ?)",
        (user.id, user.first_name)
    )
    conn.commit()

    await update.message.reply_text(
        "سلام 👋 به ربات انجمن علمی رادیولوژی خوش اومدی"
    )


# ---------------- EVENTS ----------------
async def events(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cursor.execute("SELECT * FROM events")
    rows = cursor.fetchall()

    if not rows:
        await update.message.reply_text("📭 فعلاً رویدادی وجود ندارد")
        return

    for r in rows:
        event_id = r[0]

        cursor.execute(
            "SELECT COUNT(*) FROM registrations WHERE event_id=?",
            (event_id,)
        )
        count = cursor.fetchone()[0]

        keyboard = [
            [
                InlineKeyboardButton("🟢 ثبت‌نام", callback_data=f"reg_{event_id}"),
                InlineKeyboardButton("👥 شرکت‌کنندگان", callback_data=f"list_{event_id}")
            ]
        ]

        if is_admin(update.effective_user.id):
            keyboard.append([
                InlineKeyboardButton("✏️ ویرایش", callback_data=f"edit_{event_id}"),
                InlineKeyboardButton("🗑 حذف", callback_data=f"del_{event_id}")
            ])

        await update.message.reply_text(
            f"🎓 {r[1]}\n📆 {r[2]}\n👥 ظرفیت: {r[3]}\n👤 ثبت‌نام شده: {count}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


# ---------------- CALLBACKS ----------------
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    user_id = query.from_user.id

    # ---------------- REGISTER ----------------
    if data.startswith("reg_"):
        event_id = int(data.split("_")[1])

        cursor.execute(
            "SELECT * FROM registrations WHERE user_id=? AND event_id=?",
            (user_id, event_id)
        )
        if cursor.fetchone():
            await query.answer("قبلاً ثبت‌نام کردی ❗", show_alert=True)
            return

        cursor.execute("SELECT capacity FROM events WHERE id=?", (event_id,))
        cap_row = cursor.fetchone()
        if not cap_row:
            return
        cap = cap_row[0]

        cursor.execute(
            "SELECT COUNT(*) FROM registrations WHERE event_id=?",
            (event_id,)
        )
        count = cursor.fetchone()[0]

        if count >= cap:
            await query.answer("ظرفیت تکمیل است ❌", show_alert=True)
            return

        cursor.execute(
            "INSERT INTO registrations (user_id, event_id) VALUES (?, ?)",
            (user_id, event_id)
        )
        conn.commit()

        await query.answer("ثبت شد ✅", show_alert=True)

    # ---------------- LIST ----------------
    elif data.startswith("list_"):
        event_id = int(data.split("_")[1])