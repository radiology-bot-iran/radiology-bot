from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
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

conn.commit()

# ---------------- CONFIG ----------------
TOKEN = "8723545702:AAFDjnjIj3-ZQ79X0y_5E4YHLtVXdqtA-SI"
ADMIN_ID = 8947941966

admin_states = {}  # مرحله‌ای کردن ثبت رویداد

# ---------------- CHECK ADMIN ----------------
def is_admin(update: Update):
    return update.effective_user.id == ADMIN_ID


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


# ---------------- ADD EVENT FLOW ----------------
async def add_event(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("⛔ دسترسی ندارید")
        return

    admin_states[update.effective_user.id] = {"step": "title"}

    await update.message.reply_text("عنوان رویداد را ارسال کن:")


# ---------------- TEXT HANDLER (FLOW) ----------------
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in admin_states:
        return

    state = admin_states[user_id]

    # مرحله 1: عنوان
    if state["step"] == "title":
        state["title"] = update.message.text
        state["step"] = "date"

        await update.message.reply_text("تاریخ رویداد را ارسال کن (مثلاً 2026-07-10):")
        return

    # مرحله 2: تاریخ
    if state["step"] == "date":
        state["date"] = update.message.text
        state["step"] = "capacity"

        await update.message.reply_text("ظرفیت را ارسال کن:")
        return

    # مرحله 3: ظرفیت
    if state["step"] == "capacity":
        try:
            capacity = int(update.message.text)

            cursor.execute(
                "INSERT INTO events (title, date, capacity) VALUES (?, ?, ?)",
                (state["title"], state["date"], capacity)
            )
            conn.commit()

            await update.message.reply_text("✅ رویداد با موفقیت ثبت شد")

        except ValueError:
            await update.message.reply_text("❌ ظرفیت باید عدد باشد")

        admin_states.pop(user_id, None)


# ---------------- SHOW EVENTS ----------------
async def events(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cursor.execute("SELECT * FROM events")
    rows = cursor.fetchall()

    if not rows:
        await update.message.reply_text("📭 فعلاً رویدادی وجود ندارد")
        return

    text = "📅 لیست رویدادها:\n\n"

    for r in rows:
        text += f"🎓 {r[1]}\n📆 {r[2]}\n👥 ظرفیت: {r[3]}\n\n"

    await update.message.reply_text(text)


# ---------------- APP ----------------
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("events", events))
app.add_handler(CommandHandler("add_event", add_event))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

print("Bot is running...")
app.run_polling()