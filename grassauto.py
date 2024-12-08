import asyncio
import random
import ssl
import json
import time
import uuid
import aiohttp
from loguru import logger
from websockets_proxy import Proxy, proxy_connect
from fake_useragent import UserAgent
from itertools import cycle
from rich.console import Console
from rich.text import Text
from rich.panel import Panel

# Constants for configuration
PROXY_API_URL = "https://www.proxy-list.download/api/v1/get?type=https"
WSS_URIS = ["wss://proxy2.wynd.network:4444/", "wss://proxy2.wynd.network:4650/"]
SERVER_HOSTNAME = "proxy2.wynd.network"
PING_INTERVAL = 5
PROXY_UPDATE_INTERVAL = 60
USER_ID_FILE = "user_ids.txt"

active_proxies = set()
available_proxies = set()
user_ids = []
console = Console()


def show_banner():
    banner_text = Text("KONTLIJO", style="bold magenta", justify="center")
    console.print(Panel(banner_text, expand=True, style="bold cyan", title="WELCOME", subtitle="by adhe222"))


def load_user_ids():
    try:
        with open(USER_ID_FILE, "r") as file:
            user_ids = [line.strip() for line in file.readlines() if line.strip()]
            logger.info(f"Loaded {len(user_ids)} User IDs from {USER_ID_FILE}")
            return user_ids
    except FileNotFoundError:
        logger.error(f"File {USER_ID_FILE} not found.")
        return []
    except Exception as e:
        logger.error(f"Error loading User IDs: {e}")
        return []


def load_proxies_from_file():
    proxies = set()
    try:
        with open("proxy.txt", "r") as file:
            for line in file:
                proxy = line.strip()
                if proxy.startswith("http://"):
                    proxy = proxy.replace("http://", "")
                if proxy:
                    proxies.add(proxy)
        logger.info(f"Loaded {len(proxies)} proxies from proxy.txt")
    except FileNotFoundError:
        logger.error("proxy.txt not found.")
    except Exception as e:
        logger.error(f"Error loading proxies from file: {e}")
    return proxies


def select_proxy_source():
    """
    Allow the user to select the proxy source: API or proxy.txt.
    """
    print("Select proxy source:")
    print("1. Load proxies from API")
    print("2. Load proxies from proxy.txt")
    choice = input("Enter your choice (1/2): ").strip()
    return choice


async def fetch_proxies():
    global available_proxies
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(PROXY_API_URL) as response:
                if response.status == 200:
                    text_data = await response.text()
                    proxies = text_data.splitlines()
                    available_proxies.update(proxies)
                    logger.info(f"Fetched {len(proxies)} proxies from API")
                else:
                    logger.error(f"Failed to fetch proxies: {response.status}")
    except Exception as e:
        logger.error(f"Error fetching proxies: {e}")


async def update_proxies_periodically():
    while True:
        await fetch_proxies()
        await asyncio.sleep(PROXY_UPDATE_INTERVAL)


async def connect_to_wss(socks5_proxy, user_id):
    global active_proxies

    if socks5_proxy in active_proxies:
        logger.warning(f"Skipping already active proxy: {socks5_proxy}")
        return

    active_proxies.add(socks5_proxy)

    user_agent = UserAgent()
    random_user_agent = user_agent.random
    device_id = str(uuid.uuid3(uuid.NAMESPACE_DNS, socks5_proxy))
    logger.info(f"Device ID: {device_id} for Proxy: {socks5_proxy} with User ID: {user_id}")

    try:
        while True:
            uri = random.choice(WSS_URIS)
            proxy = Proxy.from_url(f"socks5://{socks5_proxy}")
            custom_headers = {"User-Agent": random_user_agent}

            async with proxy_connect(uri, proxy=proxy, ssl=ssl.create_default_context(),
                                     server_hostname=SERVER_HOSTNAME, extra_headers=custom_headers) as websocket:
                while True:
                    response = await websocket.recv()
                    logger.info(f"Received message: {response}")
    except Exception as e:
        logger.error(f"Error with proxy {socks5_proxy}: {e}")
        active_proxies.discard(socks5_proxy)


async def main():
    global user_ids

    show_banner()

    user_ids = load_user_ids()
    if not user_ids:
        logger.error("No User IDs loaded. Exiting...")
        return

    choice = select_proxy_source()
    if choice == "1":
        logger.info("Selected proxy source: API")
        asyncio.create_task(update_proxies_periodically())
    elif choice == "2":
        logger.info("Selected proxy source: proxy.txt")
        global available_proxies
        available_proxies.update(load_proxies_from_file())
    else:
        logger.error("Invalid choice. Exiting...")
        return

    while True:
        new_proxies = available_proxies - active_proxies
        tasks = []
        for i, proxy in enumerate(new_proxies):
            user_id = user_ids[i % len(user_ids)]
            tasks.append(asyncio.create_task(connect_to_wss(proxy, user_id)))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        await asyncio.sleep(10)


if __name__ == '__main__':
    asyncio.run(main())
