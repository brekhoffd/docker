import asyncio
import json
import logging
import os
import platform
import subprocess

from dotenv import load_dotenv
from telegram import Bot


# --------------------------------------------------
# CONFIG
# --------------------------------------------------

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not found in .env")

if not CHAT_ID:
    raise ValueError("CHAT_ID not found in .env")

with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

with open("devices.json", "r", encoding="utf-8") as f:
    DEVICES = json.load(f)

CHECK_INTERVAL = config.get("check_interval", 180)

# Скільки перевірок поспіль має не пройти,
# щоб пристрій вважався OFFLINE
FAIL_THRESHOLD = config.get("fail_threshold", 3)


# --------------------------------------------------
# LOGGING
# --------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)


# --------------------------------------------------
# TELEGRAM
# --------------------------------------------------

bot = Bot(token=BOT_TOKEN)


# --------------------------------------------------
# STATE STORAGE
# --------------------------------------------------

states = {}
failures = {}


# --------------------------------------------------
# PING
# --------------------------------------------------

def ping(ip: str) -> bool:
    """
    Returns True if host responds to ping.
    """

    if platform.system().lower() == "windows":
        command = [
            "ping",
            "-n", "3",
            "-w", "1000",
            ip
        ]
    else:
        command = [
            "ping",
            "-c", "3",
            "-W", "1",
            ip
        ]

    result = subprocess.run(
        command,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    return result.returncode == 0


async def ping_async(ip: str) -> bool:
    return await asyncio.to_thread(ping, ip)


# --------------------------------------------------
# TELEGRAM MESSAGES
# --------------------------------------------------

async def send_message(text: str):
    try:
        await bot.send_message(
            chat_id=CHAT_ID,
            text=text
        )
    except Exception as e:
        logger.error(f"Telegram error: {e}")


async def send_startup_status():
    report = []

    tasks = {
        name: asyncio.create_task(ping_async(ip))
        for name, ip in DEVICES.items()
    }

    for name, ip in DEVICES.items():

        status = await tasks[name]

        states[name] = status
        failures[name] = 0

        icon = "🟢" if status else "🔴"

        report.append(
            f"{icon} {name} ({ip})"
        )

    await send_message(
        "📡 Monitoring started\n\n"
        + "\n".join(report)
    )


# --------------------------------------------------
# MONITORING
# --------------------------------------------------

async def check_devices():

    tasks = {
        name: asyncio.create_task(
            ping_async(ip)
        )
        for name, ip in DEVICES.items()
    }

    for name, ip in DEVICES.items():

        try:
            current_status = await tasks[name]

            if current_status:

                failures[name] = 0

                if not states.get(name, True):

                    states[name] = True

                    msg = (
                        f"🟢 ONLINE\n\n"
                        f"{name}\n"
                        f"{ip}"
                    )

                    logger.info(msg)
                    await send_message(msg)

            else:

                failures[name] = failures.get(name, 0) + 1

                if (
                    failures[name] >= FAIL_THRESHOLD
                    and states.get(name, True)
                ):

                    states[name] = False

                    msg = (
                        f"🔴 OFFLINE\n\n"
                        f"{name}\n"
                        f"{ip}"
                    )

                    logger.warning(msg)
                    await send_message(msg)

        except Exception as e:
            logger.error(
                f"Error checking {name} ({ip}): {e}"
            )


async def monitor():

    await send_startup_status()

    while True:

        await check_devices()

        await asyncio.sleep(CHECK_INTERVAL)


# --------------------------------------------------
# MAIN
# --------------------------------------------------

async def main():

    try:
        logger.info("Monitoring started")

        await monitor()

    finally:
        try:
            await bot.shutdown()
        except Exception:
            pass


if __name__ == "__main__":
    asyncio.run(main())
