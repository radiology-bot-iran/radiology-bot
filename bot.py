from telegram import Update from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from database import conn, cursor
TOKEN = "8723545702:AAFDjnjIj3-ZQ79X0y_5E4YHLtVXdqtA-SI"
ADMIN_ID = 8947941966
def is_admin(update): return update.effective_user.id == ADMIN_ID
---------------- START ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE): user = update.message.from_user
cursor.execute( "INSERT OR IGNORE INTO users (user_id, name) VALUES (?, ?)", (user.id, user.first_name) ) conn.commit() await update.message.reply_text( "سلام 👋 به ربات انجمن علمی رادیولوژی خوش اومدی" )
---------------- EVENTS ----------------
async def events(update: Update, context: ContextTypes.DEFAULT_TYPE):
cursor.execute("SELECT * FROM events") rows = cursor.fetchall() if not rows: await update.message.reply_text("📭 فعلاً رویدادی وجود ندارد") return text = "📅 لیست رویدادها:\n\n" for r in rows: text += f"🎓 {r[1]}\n📆 {r[2]}\n👥 ظرفیت: {r[3]}\n\n" await update.message.reply_text(text)
---------------- ADMIN PANEL ----------------
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
if not is_admin(update): await update.message.reply_text("⛔ دسترسی ندارید") return text = """
🛠 پنل مدیریت انجمن علمی
📅 /events مشاهده رویدادها
👥 /users مشاهده کاربران
💬 /view_suggestions مشاهده پیشنهادات
🚧 بخش‌های بعدی: ➕ افزودن رویداد ✏️ ویرایش رویداد 🗑 حذف رویداد 📚 مدیریت جزوات 🧪 مدیریت آزمون‌ها """
await update.message.reply_text(text)
---------------- USERS ----------------
async def users(update: Update, context: ContextTypes.DEFAULT_TYPE):
if not is_admin(update): return cursor.execute("SELECT * FROM users") rows = cursor.fetchall() text = f"👥 تعداد کاربران: {len(rows)}\n\n" for row in rows: text += f"{row[0]} - {row[1]}\n" await update.message.reply_text(text[:4000])
---------------- SUGGESTIONS ----------------
async def view_suggestions(update: Update, context: ContextTypes.DEFAULT_TYPE):
if not is_admin(update): return try: cursor.execute("SELECT * FROM suggestions") rows = cursor.fetchall() if not rows: await update.message.reply_text("📭 پیشنهادی ثبت نشده") return text = "💬 پیشنهادات کاربران:\n\n" for row in rows: text += f"{row[2]}\n\n" await update.message.reply_text(text[:4000]) except: await update.message.reply_text( "⚠️ جدول suggestions هنوز ساخته نشده است" )
---------------- APP ----------------
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start)) app.add_handler(CommandHandler("events", events)) app.add_handler(CommandHandler("admin", admin)) app.add_handler(CommandHandler("users", users)) app.add_handler(CommandHandler("view_suggestions", view_suggestions))
print("Bot is running...")
app.run_polling()