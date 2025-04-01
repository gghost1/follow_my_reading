import os
import aiohttp
from telegram import (
    Update, ReplyKeyboardMarkup, InlineKeyboardMarkup,
    InlineKeyboardButton, WebAppInfo, KeyboardButton
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
        ["📤 Загрузить PDF", "📚 Открыть приложение"],
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
    
    elif text == "📚 Открыть приложение":
        pdf_id = "abc123"  # Подставь свой PDF ID здесь
        web_app_url = MINI_APP

        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="Открыть приложение 📚", web_app=WebAppInfo(url=web_app_url))]
            ],
            resize_keyboard=True,
            one_time_keyboard=True
        )

        await update.message.reply_text(
            "Нажмите кнопку ниже, чтобы открыть Mini App:",
            reply_markup=keyboard
        )
        

    else:
        await update.message.reply_text("Выбери действие с клавиатуры ⬇️", reply_markup=main_keyboard)

# --- Загрузка PDF / Текста ---
async def handle_pdf_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = context.user_data.get("user_id", str(update.effective_user.id))

    if update.message.document:
        file = await update.message.document.get_file()
        file_bytes = await file.download_as_bytearray()
        filename = update.message.document.file_name

        async with aiohttp.ClientSession() as session:
            data = aiohttp.FormData()
            data.add_field("file", file_bytes, filename=filename, content_type='application/pdf')
            data.add_field("user_id", user_id)

            async with session.post(f"{API_BASE}/upload_pdf", data=data) as resp:
                result = await resp.json()

        await update.message.reply_text(f"✅ PDF загружен! ID: {result['pdf_id']}", reply_markup=main_keyboard)
        return ConversationHandler.END

    elif update.message.text:
        async with aiohttp.ClientSession() as session:
            data = aiohttp.FormData()
            data.add_field("text", update.message.text)
            data.add_field("user_id", user_id)

            async with session.post(f"{API_BASE}/upload_pdf", data=data) as resp:
                result = await resp.json()

        await update.message.reply_text(f"✅ Текст сохранён как PDF! ID: {result['pdf_id']}", reply_markup=main_keyboard)
        return ConversationHandler.END

    else:
        await update.message.reply_text("Пожалуйста, пришли PDF или текст.")
        return UPLOAD_PDF

# --- Список PDF ---
async def list_pdfs(update_or_query, context, only_mine=False, page=1):
    user_id = str(update_or_query.effective_user.id)
    is_callback = hasattr(update_or_query, 'callback_query')
    if hasattr(update_or_query, 'callback_query') and update_or_query.callback_query:
        message = update_or_query.callback_query.message
    else:
        message = update_or_query.message


    async with aiohttp.ClientSession() as session:
        async with session.get(f"{API_BASE}/pdfs", params={
            "page": page,
            "only_mine": str(only_mine).lower(),
            "user_id": user_id
        }) as resp:
            data = await resp.json()

    buttons = []
    for item in data["items"]:
        buttons.append([
            InlineKeyboardButton(item["text"][:30], callback_data=f"pdf_{item['pdf_id']}")
        ])

    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"page_{page-1}_{only_mine}"))
    if page * data["page_size"] < data["total"]:
        nav_buttons.append(InlineKeyboardButton("➡️ Далее", callback_data=f"page_{page+1}_{only_mine}"))
    if nav_buttons:
        buttons.append(nav_buttons)

    await message.reply_text(
        "📄 Найденные тексты:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    return ConversationHandler.END

# --- Выбор PDF ---
async def handle_pdf_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    pdf_id = query.data.replace("pdf_", "")
    context.user_data["pdf_id"] = pdf_id
    context.user_data["uploader_id"] = str(query.from_user.id)

    keyboard = [
        [InlineKeyboardButton("🎙 Озвучить", callback_data=f"record_{pdf_id}")],
        # [InlineKeyboardButton("▶️ Послушать озвучки", callback_data=f"listen_{pdf_id}")],
        [InlineKeyboardButton("▶️ Послушать озвучки", web_app=WebAppInfo(url=f"{MINI_APP}/{pdf_id}"))],
    ]

    await query.message.reply_text(
        "Что хотите сделать с этим текстом?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
async def handle_record_audio_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    pdf_id = query.data.replace("record_", "")
    context.user_data["pdf_id"] = pdf_id
    context.user_data["uploader_id"] = str(query.from_user.id)

    await query.message.reply_text("🎙 Пришлите озвучку в виде голосового сообщения.")
    return UPLOAD_AUDIO



# --- Загрузка аудио ---
async def handle_audio_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pdf_id = context.user_data.get("pdf_id")
    uploader_id = context.user_data.get("uploader_id")

    if update.message.voice or update.message.audio:
        file = await update.message.voice.get_file() if update.message.voice else await update.message.audio.get_file()
        file_bytes = await file.download_as_bytearray()
        filename = "voice.ogg" if update.message.voice else "audio.mp3"

        async with aiohttp.ClientSession() as session:
            data = aiohttp.FormData()
            data.add_field("audio", file_bytes, filename=filename, content_type="audio/ogg")
            data.add_field("uploader_id", uploader_id)

            async with session.post(f"{API_BASE}/upload_audio/{pdf_id}", data=data) as resp:
                if resp.status != 200:
                    print(resp)
                    await update.message.reply_text("❌ Ошибка при отправке аудио на сервер.")
                    return ConversationHandler.END

                result = await resp.json()
        
        keyboard = [
            [InlineKeyboardButton("▶️ Послушать эту озвучку", web_app=WebAppInfo(url=f"{MINI_APP}/{pdf_id}"))],
        ]

        await update.message.reply_text("✅ Аудио загружено и проанализировано!", reply_markup=InlineKeyboardMarkup(keyboard))
        
        return ConversationHandler.END

    else:
        await update.message.reply_text("Пожалуйста, отправьте голосовое или аудиосообщение.")
        return UPLOAD_AUDIO


# --- Страницы (пагинация) ---
async def handle_page_navigation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    _, page_str, only_mine_str = query.data.split("_")
    page = int(page_str)
    only_mine = only_mine_str == "True"
    return await list_pdfs(update, context, only_mine=only_mine, page=page)

# --- Запуск ---
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.TEXT, handle_main_menu),
            CallbackQueryHandler(handle_record_audio_request, pattern="^record_"),  # ✅ добавляем это!
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
