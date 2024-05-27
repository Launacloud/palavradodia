import os
import requests
import xml.etree.ElementTree as ET

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN_PALAVRADODIA')
RSS_FEED_URL = os.getenv('RSS_FEED_URLPALAVRADODIA')
CHAT_ID = os.getenv('TELEGRAM_CHAT_IDPALAVRADODIA')

def send_message(bot_token, chat_id, text):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'HTML'
    }
    response = requests.post(url, data=payload)
    return response

def parse_rss(feed_url):
    response = requests.get(feed_url)
    root = ET.fromstring(response.content)
    items = []
    for item in root.findall('.//item'):
        title = item.find('title').text
        link = item.find('link').text
        items.append({'title': title, 'link': link})
    return items

def main():
    rss_items = parse_rss(RSS_FEED_URL)
    for item in rss_items:
        message = f"<b>{item['title']}</b>\n{item['link']}"
        send_message(TELEGRAM_BOT_TOKEN, CHAT_ID, message)
        print(f"Sent message: {message}")
        print(f"RSS Item - Title: {item['title']}, Link: {item['link']}")

if __name__ == "__main__":
    main()
