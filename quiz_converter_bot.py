import json
import io
import re
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = "8424951624:AAH5kqadTIofTAAZsRgwZTQkU-2hqjW7niQ"

sessions = {}  # key: chat_id, value: {"quizzes": [], "filename": None}

# /baslayiriq komandası
async def start_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    sessions[chat_id] = {"quizzes": [], "filename": None}
    await update.message.reply_text(
        "Quiz seansı başladı! Quiz-ləri göndərə bilərsən.\n\n"
        "İndi fayl adı göndər."
    )

# Fayl adı mesajı
async def set_filename(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id not in sessions:
        return  # seans başlamayıb
    if sessions[chat_id]["filename"] is None:
        filename = update.message.text.strip()
        if not filename.endswith(".json"):
            filename += ".json"
        sessions[chat_id]["filename"] = filename
        await update.message.reply_text(f"Fayl adı təyin edildi: {filename}")
        return

# /bitirdik komandası - fayl şəklində JSON göndərir
async def end_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id not in sessions or len(sessions[chat_id]["quizzes"]) == 0:
        await update.message.reply_text("Heç bir quiz göndərilməyib.")
        return

    json_str = json.dumps(sessions[chat_id]["quizzes"], ensure_ascii=False, indent=2)
    bio = io.BytesIO()
    bio.write(json_str.encode('utf-8'))
    bio.seek(0)

    filename = sessions[chat_id]["filename"] or "quiz.json"
    await update.message.reply_document(document=bio, filename=filename)

    sessions[chat_id] = {"quizzes": [], "filename": None}  # session-u sıfırla

# Poll mesajlarını JSON-a çevirən funksiya
async def handle_poll_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id not in sessions:
        await update.message.reply_text("Quiz seansı başlamayıb. /baslayiriq yazın.")
        return

    poll = update.message.poll
    question_text = re.sub(r"^\[\d+/\d+\]\s*", "", poll.question)
    options = {chr(97 + i): opt.text for i, opt in enumerate(poll.options)}
    correct_index = poll.correct_option_id
    correct_key = chr(97 + correct_index) if correct_index is not None else None
    quiz_json = {
        "type": "SINGLE_CHOICE",
        "questionText": question_text,
        "options": options,
        "correctAnswer": correct_key
    }

    sessions[chat_id]["quizzes"].append(quiz_json)
    await update.message.reply_text("Quiz əlavə edildi ✅")

# Bot qurulması
app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("baslayiriq", start_quiz))
app.add_handler(CommandHandler("bitirdik", end_quiz))
app.add_handler(MessageHandler(filters.POLL, handle_poll_message))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, set_filename))

print("Bot işə düşdü...")
app.run_polling()