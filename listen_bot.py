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

def remove_chat_id(chat_id, filepath="chat_ids.txt"):
    if not os.path.exists(filepath):
        return
    with open(filepath, "r") as f:
        chat_ids = [line.strip() for line in f if line.strip()]
    chat_ids = [cid for cid in chat_ids if cid != str(chat_id)]
    with open(filepath, "w") as f:
        for cid in chat_ids:
            f.write(cid + "\n")

async def start(update, context):
    chat_id = update.effective_chat.id
    save_chat_id(chat_id)
    await update.message.reply_text("你好，每日早上将为你推送消息！")

async def unsubscribe(update, context):
    chat_id = update.effective_chat.id
    remove_chat_id(chat_id)
    await update.message.reply_text("你已取消订阅，将不再收到推送。")

async def echo(update, context):
    chat_id = update.effective_chat.id
    save_chat_id(chat_id)
    await update.message.reply_text("你好，每日早上将为你推送消息！")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("unsubscribe", unsubscribe))  # 新增
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    app.run_polling()

if __name__ == '__main__':
    main()