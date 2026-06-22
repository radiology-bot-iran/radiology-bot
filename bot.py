from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = "8723545702:AAFDjnjIj3-ZQ79X0y_5E4YHLtVXdqtA-SI"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
await update.message.reply_text("سلام")

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))

app.run_polling()