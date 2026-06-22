from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)
import sqlite3

# ================= DATABASE =================
conn = sqlite3.connect("bot.db", check_same_thread=False)
cursor = conn.cursor()

# ================= TABLES =================
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

cursor.execute("""
CREATE TABLE IF NOT EXISTS quizzes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT,
    answer TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS materials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    content TEXT
)
""")

conn.commit()

# ================= CONFIG =================
TOKEN = "8723545702:AAGF2-dS6_WXIxXJjf83bjkNI2HSV_TbP88"
ADMIN_ID = 8947941966

state = {}

# ================= ADMIN CHECK =================
def is_admin(user_id):
    return user_id == ADMIN_ID


# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user

    cursor.execute("INSERT OR IGNORE INTO users VALUES (?, ?)", (user.id, user.first_name))
    conn.commit()

    await update.message.reply_text("👋 ربات انجمن علمی رادیولوژی فعال شد")


# ================= MAIN MENU =================
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    keyboard = [
        [InlineKeyboardButton("📅 رویدادها", callback_data="menu_events")],
        [InlineKeyboardButton("📢 پیام همگانی", callback_data="menu_broadcast")],
        [InlineKeyboardButton("🧪 آزمون", callback_data="menu_quiz")],
        [InlineKeyboardButton("📚 جزوه", callback_data="menu_docs")],
        [InlineKeyboardButton("👥 آمار", callback_data="menu_stats")]
    ]

    await update.message.reply_text(
        "🛠 پنل ادمین حرفه‌ای",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ================= CALLBACK MENU =================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    user_id = query.from_user.id

    # -------- MENU --------
    if data == "menu_stats":
        cursor.execute("SELECT COUNT(*) FROM users")
        users = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM registrations")
        regs = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM quizzes")
        q = cursor.fetchone()[0]

        await query.message.reply_text(
            f"""📊 آمار سیستم:

👥 کاربران: {users}
📝 ثبت‌نام‌ها: {regs}
🧪 آزمون‌ها: {q}
"""
        )

    elif data == "menu_broadcast":
        state[user_id] = {"mode": "broadcast"}
        await query.message.reply_text("📢 پیام همگانی را ارسال کنید:")

    elif data == "menu_docs":
        cursor.execute("SELECT * FROM materials")
        rows = cursor.fetchall()

        text = "📚 جزوه‌ها:\n\n"
        for r in rows:
            text += f"📄 {r[1]}\n"

        await query.message.reply_text(text)

    elif data == "menu_quiz":
        cursor.execute("SELECT * FROM quizzes ORDER BY RANDOM() LIMIT 1")
        q = cursor.fetchone()

        if not q:
            await query.message.reply_text("🧪 آزمونی وجود ندارد")
            return

        state[user_id] = {"quiz": q}
        await query.message.reply_text(f"🧪 سوال:\n\n{q[1]}")


# ================= TEXT HANDLER =================
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    if user_id not in state:
        return

    data = state[user_id]

    # -------- BROADCAST --------
    if data.get("mode") == "broadcast":
        cursor.execute("SELECT user_id FROM users")
        users = cursor.fetchall()

        for u in users:
            try:
                await context.bot.send_message(u[0], f"📢 {text}")
            except:
                pass

        state.pop(user_id)
        await update.message.reply_text("✅ ارسال شد")

    # -------- QUIZ --------
    elif "quiz" in data:
        q = data["quiz"]

        if text.lower() == q[2].lower():
            await update.message.reply_text("✅ درست")
        else:
            await update.message.reply_text(f"❌ اشتباه\nجواب: {q[2]}")

        state.pop(user_id)


# ================= START HANDLERS =================
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin))

    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    print("🚀 Bot Pro 3 is running...")
    app.run_polling()


if __name__ == "__main__":
    main()