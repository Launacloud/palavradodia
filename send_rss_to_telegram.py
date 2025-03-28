import os
import json
import requests
import feedparser
from bs4 import BeautifulSoup

# Load environment variables
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
RSS_FEED_URL = os.getenv('RSS_FEED_URL')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# Check if environment variables are set
if not TELEGRAM_BOT_TOKEN or not RSS_FEED_URL or not CHAT_ID:
    raise ValueError("Please set TELEGRAM_BOT_TOKEN, RSS_FEED_URL, and TELEGRAM_CHAT_ID environment variables.")

# Cache file path
CACHE_FILE_PATH = 'feed_cache.json'

# Function to load cache from the file
def load_cache():
    if os.path.exists(CACHE_FILE_PATH):
        try:
            with open(CACHE_FILE_PATH, 'r') as file:
                cache = json.load(file)
                print(f"Cache loaded: {cache}")
                return cache
        except json.JSONDecodeError:
            print("Invalid JSON in cache file. Starting with an empty cache.")
            return {"etag": "", "modified": "", "processed_entries": []}
    else:
        print("No cache file found. Starting with an empty cache.")
        return {"etag": "", "modified": "", "processed_entries": []}

# Function to save cache to the file
def save_cache(cache):
    with open(CACHE_FILE_PATH, 'w') as file:
        json.dump(cache, file, indent=4)
    print(f"Cache saved: {cache}")

# Function to send a message to a Telegram chat
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': CHAT_ID,
        'text': message,
        'parse_mode': 'HTML',
        'disable_web_page_preview': 'false'
    }
    response = requests.post(url, data=payload)
    print(f"Telegram response: {response.status_code} - {response.text}")
    if response.status_code != 200:
        raise Exception(f"Error sending message: {response.text}")

# Function to create a feed checker
def create_feed_checker(feed_url):
    def check_feed():
        cache = load_cache()
        processed_entries = cache.get("processed_entries", [])
        print(f"Processed entries from cache: {processed_entries}")

        headers = {}
        if cache["etag"]:
            headers['If-None-Match'] = cache["etag"]
        if cache["modified"]:
            headers['If-Modified-Since'] = cache["modified"]

        response = requests.get(feed_url, headers=headers)
        print(f"Feed request status: {response.status_code}")
        if response.status_code == 304:
            print("Feed not modified since last check.")
            return

        feed = feedparser.parse(response.content)
        print(f"Feed entries count: {len(feed.entries)}")

        if 'etag' in response.headers:
            cache["etag"] = response.headers['etag']
        if 'last-modified' in response.headers:
            cache["modified"] = response.headers['last-modified']

        new_entries = []
        for entry in feed.entries:
            entry_id = entry.get('id', entry.get('link')).strip()
            print(f"Checking entry ID: {entry_id}")
            if entry_id not in processed_entries:
                new_entries.append(entry)
                print(f"New entry found: {entry_id}")
            else:
                print(f"Entry already processed: {entry_id}")

        if not new_entries:
            print("No new entries to process.")
            return

        # Process only the most recent new entry
        entry = new_entries[-1]  # Take the latest entry
        entry_id = entry.get('id', entry.get('link')).strip()
        print(f"Processing single entry: {entry_id}")

        title = entry.title
        link = entry.get('link', entry.get('url'))
        description = entry.get('content_html', entry.get('description', ''))

        if description:
            soup = BeautifulSoup(description, 'html.parser')
            supported_tags = ['b', 'i', 'a']
            for tag in soup.find_all():
                if tag.name not in supported_tags:
                    tag.decompose()
            description_text = soup.prettify()
        else:
            description_text = "No description available."

        message = f"<b>{title}</b>\n<a href='{link}'>{link}</a>\n\n{description_text}"
        
        try:
            send_telegram_message(message)
            processed_entries.append(entry_id)
            cache["processed_entries"] = processed_entries
            save_cache(cache)
        except Exception as e:
            print(f"Error sending message: {e}")

    return check_feed

# Main function
def main():
    try:
        check_feed = create_feed_checker(RSS_FEED_URL)
        check_feed()
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()
