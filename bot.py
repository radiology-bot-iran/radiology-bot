from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import sqlite3

# ---------------- DATABASE ----------------
conn = sqlite3.connect("bot.db", check_same_thread=False)
cursor = conn.cursor()

# اگر جدول events وجود ندارد
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
TOKEN = "8723545702:AAGF2-dS6_WXIxXJjf83bjkNI2HSV_TbP88"
ADMIN_ID = 8947941966

# ---------------- START ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام 👋 ربات فعال شد")

# ---------------- EVENTS ----------------
async def events(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cursor.execute("SELECT * FROM events")
    rows = cursor.fetchall()

    if not rows:
        await update.message.reply_text("📭 هیچ رویدادی وجود ندارد")
        return

    text = "📅 رویدادها:\n\n"

    for r in rows:
        text += f"🎓 {r[1]}\n📆 {r[2]}\n👥 ظرفیت: {r[3]}\n\n"

    await update.message.reply_text(text)

# ---------------- MAIN APP ----------------
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("events", events))

    print("Bot is running...")
    app.run_polling()
