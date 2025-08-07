import os
from telegram.ext import Application, CommandHandler, MessageHandler, filters
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
        print(f"新增订阅 chat_id: {chat_id}")
    else:
        print(f"重复订阅 chat_id: {chat_id}")

def remove_chat_id(chat_id, filepath="chat_ids.txt"):
    if not os.path.exists(filepath):
        return
    with open(filepath, "r") as f:
        chat_ids = [line.strip() for line in f if line.strip()]
    if str(chat_id) in chat_ids:
        chat_ids = [cid for cid in chat_ids if cid != str(chat_id)]
        with open(filepath, "w") as f:
            for cid in chat_ids:
                f.write(cid + "\n")
        print(f"已取消订阅 chat_id: {chat_id}")
    else:
        print(f"chat_id: {chat_id} 不在订阅列表中")

async def start(update, context):
    chat_id = update.effective_chat.id
    save_chat_id(chat_id)
    print(f"/start 来自 chat_id: {chat_id}")
    await update.message.reply_text("你好，每日早上将为你推送消息！\n如需退订请发送 /unsubscribe")

async def unsubscribe(update, context):
    chat_id = update.effective_chat.id
    remove_chat_id(chat_id)
    print(f"/unsubscribe 来自 chat_id: {chat_id}")
    await update.message.reply_text("你已取消订阅，将不再收到推送。")

async def echo(update, context):
    chat_id = update.effective_chat.id
    save_chat_id(chat_id)
    print(f"收到消息 from chat_id: {chat_id}，内容：{update.message.text}")
    await update.message.reply_text("你好，每日早上将为你推送消息！\n如需退订请发送 /unsubscribe")

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
