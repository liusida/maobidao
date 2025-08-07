from telegram.ext import Application, CommandHandler, MessageHandler, filters
import os
from dotenv import load_dotenv
load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

def save_chat_id(chat_id, filepath="chat_ids.txt"):
    if not os.path.exists(filepath):
        open(filepath, "w").close()
    with open(filepath, "r") as f:
        chat_ids = set(line.strip() for line in f if line.strip())
    if str(chat_id) not in chat_ids:
        with open(filepath, "a") as f:
            f.write(str(chat_id) + "\n")

async def start(update, context):
    chat_id = update.effective_chat.id
    save_chat_id(chat_id)
    await update.message.reply_text("你好，你的 chat_id 已保存！")

async def echo(update, context):
    chat_id = update.effective_chat.id
    save_chat_id(chat_id)
    await update.message.reply_text("已收到你的消息，chat_id 已保存！")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    app.run_polling()

if __name__ == '__main__':
    main()
