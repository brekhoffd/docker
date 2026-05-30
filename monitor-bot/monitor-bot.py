import asyncio
import json
import os
import platform
import subprocess

from dotenv import load_dotenv
from telegram import Bot

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

with open("devices.json", "r", encoding="utf-8") as f:
    DEVICES = json.load(f)

CHECK_INTERVAL = config.get("check_interval", 180)

bot = Bot(token=BOT_TOKEN)

states = {}


def ping(ip: str) -> bool:
    if platform.system().lower() == "windows":
        command = ["ping", "-n", "3", ip]
    else:
        command = ["ping", "-c", "3", ip]

    result = subprocess.run(
        command,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    return result.returncode == 0


async def send_message(text: str):
    try:
        await bot.send_message(
            chat_id=CHAT_ID,
            text=text
        )
    except Exception as e:
        print(f"Telegram error: {e}")


async def send_startup_status():
    report = []

    for name, ip in DEVICES.items():

        status = ping(ip)

        states[name] = status

        icon = "🟢" if status else "🔴"

        report.append(
            f"{icon} {name} ({ip})"
        )

    await send_message(
        "📡 Monitoring started\n\n"
        + "\n".join(report)
    )


async def monitor():

    await send_startup_status()

    while True:

        for name, ip in DEVICES.items():

            current_status = ping(ip)

            if current_status != states[name]:

                states[name] = current_status

                if current_status:
                    msg = (
                        f"🟢 ONLINE\n\n"
                        f"{name}\n"
                        f"{ip}"
                    )
                else:
                    msg = (
                        f"🔴 OFFLINE\n\n"
                        f"{name}\n"
                        f"{ip}"
                    )

                print(msg)

                await send_message(msg)

        await asyncio.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    asyncio.run(monitor())
