#!/usr/bin/env python3

import os
import requests
from bs4 import BeautifulSoup
import openai
import json
import re
import datetime
import hashlib
from dotenv import load_dotenv
import asyncio
from telegram import Bot

# 1. Load config (API keys, tokens) from .env
load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
client = openai.OpenAI(api_key=OPENAI_API_KEY)

# 2. Get latest article info using GPT-4o-mini
def get_latest_article():
    url = 'https://www.maobidao.net/'
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    html = response.text[:20000]  # Truncate to avoid token limit
    utc_now = datetime.datetime.now(datetime.timezone.utc)
    beijing_now = utc_now + datetime.timedelta(hours=8)
    now_str = beijing_now.strftime("%Y-%m-%d %H:%M")

    prompt = (
        f"你是一个帮助从网页HTML中提取文章信息的助手。\n"
        f"当前北京时间为：{now_str}\n"
        "请从下面的HTML代码中，提取最新一篇文章的标题、链接和发布时间，"
        "并以JSON格式返回（格式为{\"title\": \"...\", \"url\": \"...\", \"time\": \"YYYY-MM-DD HH:mm\"}）。\n\n"
        "HTML内容如下：\n"
        f"{html}\n"
        "\n只返回JSON结果，不要输出其他内容。"
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300,
        temperature=0.0,
    )

    content = None
    if hasattr(response, "choices") and response.choices and hasattr(response.choices[0], "message"):
        content = response.choices[0].message.content
    else:
        print("OpenAI 返回内容结构异常：", response)
        raise RuntimeError("OpenAI 返回结果不含 choices 字段")
    match = re.search(r"\{.*\}", content, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group())
            return data["title"], data["url"], data["time"]
        except Exception as e:
            print(f"JSON解析失败: {e}")
            print(f"AI返回内容: {content}")
            raise
    else:
        print("未找到JSON对象，AI原始返回：", content)
        raise ValueError("AI响应中未找到有效的JSON对象")

# 3. Fetch and cache article HTML
def get_cached_html(link, cache_dir="article_html_cache"):
    os.makedirs(cache_dir, exist_ok=True)
    filename = hashlib.md5(link.encode("utf-8")).hexdigest() + ".html"
    path = os.path.join(cache_dir, filename)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            html = f.read()
        return html
    resp = requests.get(link, timeout=10)
    resp.raise_for_status()
    html = resp.text
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    return html

# 4. Extract all <section> text as main content
def extract_main_text_from_all_sections(html):
    soup = BeautifulSoup(html, "html.parser")
    sections = soup.find_all("section")
    if sections:
        article_text = "\n".join(
            section.get_text(separator="\n", strip=True)
            for section in sections
        )
        return article_text[:4000]  # 截断防止token过多
    else:
        print("没有找到<section>标签。")
        return ""

def extract_json_array(text):
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group())
            return data
        except Exception as e:
            print("JSON解析失败:", e)
            print("AI原始输出:", text)
            return []
    else:
        print("未找到JSON数组，AI原始输出:", text)
        return []

# 5. Extract mentioned companies with sentiment from article text using GPT-4o-mini
def extract_mentioned_companies(link):
    html = get_cached_html(link)
    article_text = extract_main_text_from_all_sections(html)
    if not article_text.strip():
        print("警告：未提取到正文内容。")
        return []

    prompt = (
        "你是专业的信息抽取助手。请从下面的文章内容中，提取所有被提及的A股上市公司名称。"
        "对于每家被提及的公司，请判断作者对该公司的未来操作观点（买入/卖出/忽略），注意忽略早期历史回顾，只抽取真正需要关注的公司。"
        "同时给出作者在提及这个公司时的整体情绪（正面/负面/中性）。\n"
        "返回格式要求如下：\n"
        "- 字段 company：公司名称\n"
        "- 字段 stance：未来操作观点，只能是“买入”“卖出”“忽略”之一\n"
        "- 字段 sentiment：情绪，只能是“正面”“负面”“中性”之一\n"
        "请以JSON数组返回（格式为：[{\"company\": \"公司名\", \"stance\": \"买入/卖出/忽略\", \"sentiment\": \"正面/负面/中性\"}, ...]）。\n"
        "如文中未提及公司，请返回空数组 []。\n"
        "只返回JSON数组，不要输出其他内容。\n\n"
        f"文章内容：\n{article_text}"
    )

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=4096,
        temperature=0.0,
    )
    content = completion.choices[0].message.content

    companies = extract_json_array(content)
    return companies

# 6. 读取所有 chat_id
def get_all_chat_ids(filepath="chat_ids.txt"):
    if not os.path.exists(filepath):
        return []
    with open(filepath, "r") as f:
        return [line.strip() for line in f if line.strip()]

# 7. 格式化推送消息
def format_message(title, link, time, companies):
    msg = f"📢 猫笔刀新文章\n\n标题：{title}\n链接：{link}\n"
    if companies:
        msg += "\n文章涉及公司：\n"
        for comp in companies:
            if isinstance(comp, dict):
                msg += f"- {comp.get('stance', '')} {comp.get('company', '')}（情绪：{comp.get('sentiment', '')}）\n"
            else:
                msg += f"- {comp}\n"
    else:
        msg += "\n未检测到公司名。"
    return msg

# 8. 异步发送推送到所有 chat_id
async def send_telegram_notification(bot_token, chat_ids, message):
    bot = Bot(token=bot_token)
    for chat_id in chat_ids:
        try:
            await bot.send_message(chat_id=chat_id, text=message)
            print(f"已发送给 {chat_id}")
        except Exception as e:
            print(f"发送给 {chat_id} 失败: {e}")

# 9. 主流程
def main():
    title, link, time = get_latest_article()
    print(f"Title: {title}\nLink: {link}\nTime: {time}")

    companies = extract_mentioned_companies(link)
    print("公司抽取结果：", companies)

    message = format_message(title, link, time, companies)
    print("推送内容：\n", message)

    chat_ids = get_all_chat_ids()
    if not chat_ids:
        print("没有找到 chat_id，推送已跳过。")
        return
    asyncio.run(send_telegram_notification(TELEGRAM_BOT_TOKEN, chat_ids, message))

if __name__ == "__main__":
    main()
