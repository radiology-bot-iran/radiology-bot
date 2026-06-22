import sqlite3
import asyncio
import time

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)

conn = sqlite3.connect("bot.db", check_same_thread=False)
cur = conn.cursor()

TOKEN = "8723545702:AAGF2-dS6_WXIxXJjf83bjkNI2HSV_TbP88"
ADMIN_ID = 8947941966

state = {}
quiz_cache = {}
answered = set()
admin_buffer = {}

# ---------------- SETTINGS ENGINE ----------------
def get_setting(key, default="30"):
    cur.execute("SELECT value FROM settings WHERE key=?", (key,))
    r = cur.fetchone()
    return r[0] if r else default

def set_setting(key, value):
    cur.execute("INSERT OR REPLACE INTO settings VALUES (?,?)", (key, str(value)))
    conn.commit()

# ---------------- MENU ----------------
def menu(uid):
    kb = [
        [InlineKeyboardButton("📝 آزمون", callback_data="quiz")],
        [InlineKeyboardButton("📩 درخواست", callback_data="req")],
        [InlineKeyboardButton("📅 رویداد", callback_data="event")],
        [InlineKeyboardButton("🏆 رتبه", callback_data="rank")]
    ]

    if uid == ADMIN_ID:
        kb.append([InlineKeyboardButton("🛠 پنل مدیریت", callback_data="admin")])

    return InlineKeyboardMarkup(kb)

# ---------------- START ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user

    cur.execute("SELECT * FROM users WHERE user_id=?", (u.id,))
    if cur.fetchone():
        await update.message.reply_text("🏠 منو", reply_markup=menu(u.id))
        return

    state[u.id] = "register"
    await update.message.reply_text("🎓 شماره دانشجویی را وارد کنید:")

# ---------------- QUIZ ENGINE ----------------
async def run_quiz(uid, msg, context):
    cur.execute("SELECT * FROM quizzes ORDER BY RANDOM() LIMIT 1")
    q = cur.fetchone()

    if not q:
        await msg.reply_text("❌ آزمون وجود ندارد")
        return

    quiz_cache[uid] = q

    time_limit = int(get_setting("quiz_time", 30))

    kb = [[
        InlineKeyboardButton("A", callback_data="A"),
        InlineKeyboardButton("B", callback_data="B"),
        InlineKeyboardButton("C", callback_data="C")
    ]]

    await msg.reply_text(
        f"""📝 {q[1]}

A) {q[2]}
B) {q[3]}
C) {q[4]}

⏱ زمان: {time_limit} ثانیه""",
        reply_markup=InlineKeyboardMarkup(kb)
    )

    await asyncio.sleep(time_limit)

    if uid in quiz_cache and uid not in answered:
        quiz_cache.pop(uid, None)
        await msg.reply_text("⛔ زمان آزمون تمام شد")

# ---------------- TEXT HANDLER ----------------
async def text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    txt = update.message.text

    # REGISTER
    if uid in state and state[uid] == "register":
        cur.execute("INSERT INTO users VALUES (?,?,?)", (uid, txt, update.effective_user.first_name))
        conn.commit()
        state.pop(uid)
        await update.message.reply_text("✅ ثبت شد", reply_markup=menu(uid))
        return

    # ADMIN SET TIME
    if uid in state and state[uid] == "set_time":
        set_setting("quiz_time", txt)
        state.pop(uid)
        await update.message.reply_text("⏱ زمان آپدیت شد")
        return

    # ADMIN REPLY
    if uid in admin_buffer:
        req_id = admin_buffer[uid]

        cur.execute("SELECT user_id FROM requests WHERE id=?", (req_id,))
        t = cur.fetchone()

        if t:
            await context.bot.send_message(t[0], f"📬 پاسخ:\n{txt}")

        cur.execute("UPDATE requests SET status='done' WHERE id=?", (req_id,))
        conn.commit()

        admin_buffer.pop(uid)
        await update.message.reply_text("✅ ارسال شد")

# ---------------- CALLBACK ----------------
async def cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    uid = q.from_user.id
    d = q.data

    # QUIZ
    if d == "quiz":
        await run_quiz(uid, q.message, context)
        return
    
    # ANSWER
    if d in ["A","B","C"]:
        if uid in answered or uid not in quiz_cache:
            return

        qz = quiz_cache[uid]
        correct = qz[5]

        cur.execute("INSERT OR IGNORE INTO results VALUES (?,?,?)", (uid,0,0))
        cur.execute("UPDATE results SET total=total+1 WHERE user_id=?", (uid,))

        if d == correct:
            cur.execute("UPDATE results SET score=score+1 WHERE user_id=?", (uid,))

        conn.commit()

        answered.add(uid)
        quiz_cache.pop(uid, None)

        await q.message.reply_text(f"✅ ثبت شد | جواب: {correct}")
        return

    # REQUEST
    if d == "req":
        cur.execute("INSERT INTO requests VALUES (NULL, ?, '', 'pending')", (uid,))
        conn.commit()
        await q.message.reply_text("✍️ پیام خود را بنویس")
        return

    # RANK
    if d == "rank":
        cur.execute("SELECT user_id, score FROM results ORDER BY score DESC LIMIT 10")
        rows = cur.fetchall()

        t = "🏆 رتبه‌بندی:\n\n"
        for i,r in enumerate(rows,1):
            t += f"{i}) {r[0]} - {r[1]}\n"

        await q.message.reply_text(t)
        return

    # ADMIN PANEL
    if d == "admin" and uid == ADMIN_ID:
        cur.execute("SELECT id FROM requests WHERE status='pending'")
        rows = cur.fetchall()

        kb = [[InlineKeyboardButton(f"📩 {r[0]}", callback_data=f"r_{r[0]}")] for r in rows]
        kb.append([InlineKeyboardButton("⏱ تغییر زمان آزمون", callback_data="set_time")])

        await q.message.reply_text("🛠 پنل مدیریت", reply_markup=InlineKeyboardMarkup(kb))
        return

    # SET TIME
    if d == "set_time":
        state[uid] = "set_time"
        await q.message.reply_text("⏱ زمان جدید (ثانیه):")
        return

    # REPLY REQUEST
    if d.startswith("r_"):
        admin_buffer[uid] = int(d.split("_")[1])
        await q.message.reply_text("✍️ پاسخ را بنویس")

# ---------------- APP ----------------
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(cb))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text))

print("🚀 INDUSTRIAL BOT RUNNING")
app.run_polling()