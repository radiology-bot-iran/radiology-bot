import sqlite3

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# ================= DB =================
conn = sqlite3.connect("bot.db", check_same_thread=False)
cur = conn.cursor()

def init_db():
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        student_id TEXT,
        name TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        date TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS quizzes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        q TEXT,
        a TEXT,
        b TEXT,
        c TEXT,
        ans TEXT
    )
    """)

    conn.commit()

# ================= CONFIG =================
TOKEN = "8723545702:AAGF2-dS6_WXIxXJjf83bjkNI2HSV_TbP88"
ADMIN_ID = 8947941966

state = {}
quiz_cache = {}

# ================= SEED =================
def seed():
    cur.execute("SELECT COUNT(*) FROM events")
    if cur.fetchone()[0] == 0:
        cur.execute("INSERT INTO events (title,date) VALUES (?,?)",
                    ("📅 سمینار MRI", "1404/06/03"))

    cur.execute("SELECT COUNT(*) FROM quizzes")
    if cur.fetchone()[0] == 0:
        cur.execute("""
        INSERT INTO quizzes (q,a,b,c,ans) VALUES
        ('MRI چیست؟','اشعه X','میدان مغناطیسی','اولتراسوند','B'),
        ('MRI برای چیست؟','استخوان','بافت نرم','ریه','B'),
        ('کنتراست MRI چیست؟','گادولینیوم','ید','آب','A')
        """)

    conn.commit()

# ================= MENU =================
def menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📅 رویدادها", callback_data="events")],
        [InlineKeyboardButton("🧪 آزمون MRI", callback_data="quiz")]
    ])

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    cur.execute("SELECT * FROM users WHERE user_id=?", (uid,))
    if not cur.fetchone():
        state[uid] = "reg"
        await update.message.reply_text("🎓 کد دانشجویی را وارد کنید:")
        return

    await update.message.reply_text("🏠 منو", reply_markup=menu())

# ================= TEXT =================
async def text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    txt = update.message.text

    # REGISTER
    if state.get(uid) == "reg":
        cur.execute("INSERT INTO users VALUES (?,?,?)",
                    (uid, txt, update.effective_user.first_name))
        conn.commit()
        state.pop(uid)

        await update.message.reply_text("✅ ثبت شد", reply_markup=menu())
        return

# ================= CALLBACK =================
async def cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    uid = q.from_user.id
    data = q.data

    # -------- EVENTS --------
    if data == "events":
        cur.execute("SELECT * FROM events")
        rows = cur.fetchall()

        if not rows:
            await q.message.reply_text("📭 رویدادی نیست")
            return

        msg = "📅 رویدادها:\n\n"
        for r in rows:
            msg += f"{r[1]} | {r[2]}\n"

        await q.message.reply_text(msg)
        return

    # -------- QUIZ --------
    if data == "quiz":
        cur.execute("SELECT * FROM quizzes ORDER BY RANDOM() LIMIT 1")
        qz = cur.fetchone()

        if not qz:
            await q.message.reply_text("❌ آزمون نیست")
            return

        quiz_cache[uid] = qz

        kb = [[
            InlineKeyboardButton("A", callback_data="A"),
            InlineKeyboardButton("B", callback_data="B"),
            InlineKeyboardButton("C", callback_data="C")
        ]]

        await q.message.reply_text(
            f"""🧪 {qz[1]}

A) {qz[2]}
B) {qz[3]}
C) {qz[4]}

⏱ 60 ثانیه فرصت""",
            reply_markup=InlineKeyboardMarkup(kb)
        )
        return
    # -------- ANSWER --------
    if data in ["A", "B", "C"]:
        if uid not in quiz_cache:
            return

        qz = quiz_cache[uid]

        if data == qz[5]:
            await q.message.reply_text("✅ درست")
        else:
            await q.message.reply_text(f"❌ غلط | جواب: {qz[5]}")

        quiz_cache.pop(uid)
        return
# ================= MAIN =================
def main():
    init_db()
    seed()

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(cb))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text))

    print("🚀 BOT FIXED RUNNING")
    app.run_polling()

if __name__ == "__main__":
    main()