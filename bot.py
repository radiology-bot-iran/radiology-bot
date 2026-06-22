from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import sqlite3

# ---------------- DATABASE ----------------
conn = sqlite3.connect("bot.db", check_same_thread=False)
cursor = conn.cursor()

# ---------------- CONFIG ----------------
TOKEN = "PUT_YOUR_TOKEN_HERE"

# ---------------- START ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user

    cursor.execute(
        "INSERT OR IGNORE INTO users (user_id, name) VALUES (?, ?)",
        (user.id, user.first_name)
    )
    conn.commit()

    await update.message.reply_text(
        "👋 سلام! ربات انجمن علمی رادیولوژی فعال شد"
    )


# ---------------- EVENTS ----------------
async def events(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cursor.execute("SELECT * FROM events")
    rows = cursor.fetchall()

    if not rows:
        await update.message.reply_text("📭 هیچ رویدادی وجود ندارد")
        return

    text = "📅 لیست رویدادها:\n\n"

    for r in rows:
        text += f"🎓 {r[1]}\n📆 {r[2]}\n👥 ظرفیت: {r[3]}\n\n"

    await update.message.reply_text(text)


# ---------------- MAIN ----------------
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("events", events))

    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()