import os
import time
import requests
import schedule
from datetime import datetime

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

CURRENCIES = ["USD", "EUR", "PLN"]

def get_exchange_rates():
    try:
        response = requests.get(
            "https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange?json",
            timeout=10
        )

        data = response.json()

        rates = {}

        for item in data:
            cc = item.get("cc")

            if cc in CURRENCIES:
                rates[cc] = item.get("rate")

        return rates

    except Exception as e:
        print("NBU API error:", e)
        return {}

def send_message():
    try:
        rates = get_exchange_rates()

        text = "✅ Server Online\n"
        text += f"🕒 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        text += "💱 Exchange Rates:\n"

        if "USD" in rates:
            text += f"🇺🇸 USD: {rates['USD']:.2f} UAH\n"

        if "EUR" in rates:
            text += f"🇪🇺 EUR: {rates['EUR']:.2f} UAH\n"

        if "PLN" in rates:
            text += f"🇵🇱 PLN: {rates['PLN']:.2f} UAH\n"

        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

        payload = {
            "chat_id": CHAT_ID,
            "text": text
        }

        response = requests.post(url, data=payload, timeout=10)

        if response.status_code == 200:
            print("Message sent")
        else:
            print("Telegram error:", response.text)

    except Exception as e:
        print("Send message error:", e)

# Send daily at 09:00
schedule.every().day.at("09:00").do(send_message)

# Test message at startup
send_message()

print("Bot started")

while True:
    try:
        schedule.run_pending()
    except Exception as e:
        print("Loop error:", e)

    time.sleep(30)
