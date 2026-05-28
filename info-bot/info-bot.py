import os
import time
import requests
import schedule
from datetime import datetime

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def send_message():
    text = f"✅ Server online\n🕒 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    payload = {
        "chat_id": CHAT_ID,
        "text": text
    }

    try:
        response = requests.post(url, data=payload, timeout=10)

        if response.status_code == 200:
            print("Message sent")
        else:
            print("Telegram error:", response.text)

    except Exception as e:
        print("Error:", e)

# Send daily at 09:00 AM
schedule.every().day.at("09:00").do(send_message)

# Test message at startup
send_message()

print("Bot started")

while True:
    schedule.run_pending()
    time.sleep(30)
