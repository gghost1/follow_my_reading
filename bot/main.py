import os
import aiohttp
from telegram import (
    Update, ReplyKeyboardMarkup, InlineKeyboardMarkup,
    InlineKeyboardButton
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, ConversationHandler, filters
)

import data

# --- Настройки ---
API_BASE = data.API_URL
BOT_TOKEN = data.TOKEN  
MINI_APP = data.MINI_APP

# --- Состояния ---
UPLOAD_PDF, UPLOAD_AUDIO = range(2)

# --- Постоянная клавиатура ---
main_keyboard = ReplyKeyboardMarkup(
    [
        ["📤 Загрузить PDF"],
        ["📚 Посмотреть доступные тексты", "📁 Посмотреть мои тексты"]
    ],
    resize_keyboard=True
)

# --- /start ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Что хочешь сделать?",
        reply_markup=main_keyboard
    )

# --- Главное меню (текст) ---
async def handle_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = str(update.effective_user.id)

    if text == "📤 Загрузить PDF":
        await update.message.reply_text("Пришли мне PDF-файл или текст.", reply_markup=main_keyboard)
        context.user_data["user_id"] = user_id
        return UPLOAD_PDF

    elif text == "📚 Посмотреть доступные тексты":
        return await list_pdfs(update, context, only_mine=False)

    elif text == "📁 Посмотреть мои тексты":
        return await list_pdfs(update, context, only_mine=True)

    else:
        await update.message.reply_text("Выбери действие с клавиатуры ⬇️", reply_markup=main_keyboard)

# --- Запуск ---
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.TEXT, handle_main_menu),
            CallbackQueryHandler(handle_record_audio_request, pattern="^record_"),  
        ],
        states={
            UPLOAD_PDF: [MessageHandler(filters.TEXT | filters.Document.PDF, handle_pdf_upload)],
            UPLOAD_AUDIO: [MessageHandler(filters.VOICE | filters.AUDIO, handle_audio_upload)],
        },
        fallbacks=[],
    )


    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(handle_pdf_selection, pattern="^pdf_"))
    app.add_handler(CallbackQueryHandler(handle_page_navigation, pattern="^page_"))
    app.add_handler(CallbackQueryHandler(handle_record_audio_request, pattern="^record_"))


    print("🤖 Бот запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()
