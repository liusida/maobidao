import asyncio
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import os
from dotenv import load_dotenv
load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

def save_chat_id(chat_id, filepath="chat_ids.txt"):
    # ...略，保持不变...

def remove_chat_id(chat_id, filepath="chat_ids.txt"):
    # ...略，保持不变...

async def start(update, context):
    # ...略...

async def unsubscribe(update, context):
    # ...略...

async def echo(update, context):
    # ...略...

async def set_my_commands(app):
    await app.bot.set_my_commands([
        ("start", "订阅推送/获取 chat_id"),
        ("unsubscribe", "取消订阅"),
    ])
    print("已注册命令菜单：/start, /unsubscribe")

def main():
    print("Maobidao listen_bot 正在启动...")
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("unsubscribe", unsubscribe))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    app.post_init = set_my_commands  # <--- 关键修复点

    print("启动轮询监听，等待消息中...")
    app.run_polling()

if __name__ == '__main__':
    main()
