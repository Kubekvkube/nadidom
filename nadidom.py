import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from dotenv import load_dotenv
import os

load_dotenv()  # Эта строка обязательно должна быть ДО os.getenv

token = os.getenv("BOT_TOKEN")


# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# States
CHOOSING, ASKING_NAME, ASKING_COUNTRY, ASKING_EXTRA = range(4)

# Data store
user_data = {}

# Admin chat ID (можно также указать ID Telegram-группы)
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")  # например, '-1001234567890'

# Inline keyboard
keyboard = [
    [InlineKeyboardButton("🏠 Find Accommodation", callback_data='accommodation')],
    [InlineKeyboardButton("📑 Apply for Visa", callback_data='visa')],
    [InlineKeyboardButton("💼 MM2H Properties", callback_data='mm2h')],
    [InlineKeyboardButton("🏢 Open Business", callback_data='business')],
    [InlineKeyboardButton("🧳 Find Activities", callback_data='activities')],
    [InlineKeyboardButton("🛜 Book Coworking", callback_data='coworking')],
]

markup = InlineKeyboardMarkup(keyboard)

# Command: /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hi 👋 How can we assist you today?",
        reply_markup=markup
    )
    return CHOOSING

# Handle category selection
async def handle_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    user_data[user_id] = {
        'category': query.data,
    }

    await query.edit_message_text("📝 Please enter your *name*:", parse_mode="Markdown")
    return ASKING_NAME

async def ask_country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_data[user_id]['name'] = update.message.text
    await update.message.reply_text("🌍 What is your *country or nationality*?", parse_mode="Markdown")
    return ASKING_COUNTRY

async def ask_extra(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_data[user_id]['country'] = update.message.text

    category = user_data[user_id]['category']
    category_question = {
        'accommodation': "🏠 How long will you stay and your budget?",
        'visa': "📑 What type of visa do you need and for how long?",
        'mm2h': "💼 What's your investment range or expectations?",
        'business': "🏢 What kind of business do you want to open?",
        'activities': "🧳 What kind of activities are you looking for?",
        'coworking': "🛜 Which city and duration for coworking?",
    }

    question = category_question.get(category, "🔍 Please provide more details")
    await update.message.reply_text(question)
    return ASKING_EXTRA

async def finish_form(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_data[user_id]['extra'] = update.message.text

    data = user_data[user_id]
    confirmation = f"""
✅ Thank you! We’ve received your request:

• Name: {data['name']}
• Country: {data['country']}
• Category: {data['category']}
• Details: {data['extra']}
"""

    await update.message.reply_text(confirmation)

    # Forward to admin or group
    if ADMIN_CHAT_ID:
        await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=confirmation)

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Cancelled. You can restart anytime with /start")
    return ConversationHandler.END

print(f"Токен: {repr(token)}")

# MAIN
def main():
    app = ApplicationBuilder().token(token).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING: [CallbackQueryHandler(handle_category)],
            ASKING_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_country)],
            ASKING_COUNTRY: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_extra)],
            ASKING_EXTRA: [MessageHandler(filters.TEXT & ~filters.COMMAND, finish_form)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
