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

PROXY_API_URLS = {
    1: ('SERVER 1', 'https://files.ramanode.top/airdrop/grass/server_1.txt'),
    2: ('SERVER 2', 'https://files.ramanode.top/airdrop/grass/server_2.txt'),
    3: ('SERVER 3', 'https://files.ramanode.top/airdrop/grass/server_3.txt'),
    4: ('SERVER 4', 'https://files.ramanode.top/airdrop/grass/server_4.txt'),
    5: ('SERVER 5', 'https://files.ramanode.top/airdrop/grass/server_5.txt'),
    6: ('SERVER 6', 'https://files.ramanode.top/airdrop/grass/server_6.txt'),
}

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

def select_api_url():
    print("Select API URL:")
    for key, (server_name, _) in PROXY_API_URLS.items():
        print(f"{key}. {server_name}")
    while True:
        try:
            choice = int(input("Enter your choice (1-6): ").strip())
            if choice in PROXY_API_URLS:
                return PROXY_API_URLS[choice][1]
            else:
                print("Invalid choice. Please select a valid option.")
        except ValueError:
            print("Invalid input. Please enter a number.")

async def fetch_proxies(api_url):
    global available_proxies
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url) as response:
                if response.status == 200:
                    text_data = await response.text()
                    proxies = text_data.splitlines()
                    processed_proxies = set()
                    for proxy in proxies:
                        if not proxy.startswith("http://"):
                            proxy = f"http://{proxy}"
                        processed_proxies.add(proxy)
                    logger.info(f"Fetched {len(processed_proxies)} proxies from {api_url}")
                    available_proxies.update(processed_proxies)
                else:
                    logger.error(f"Failed to fetch proxies from {api_url} - Status {response.status}")
    except Exception as e:
        logger.error(f"Error fetching proxies from {api_url}: {e}")

async def update_proxies_periodically(api_url):
    while True:
        await fetch_proxies(api_url)
        await asyncio.sleep(PROXY_UPDATE_INTERVAL)

async def animate_ping_pong(action):
    animation = cycle(['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'])
    for _ in range(10):
        print(f"\r{action} {next(animation)}", end='', flush=True)
        await asyncio.sleep(0.1)
    print("\r", end='', flush=True)

async def connect_to_wss(socks5_proxy, user_id):
    global active_proxies, available_proxies
    if socks5_proxy in active_proxies:
        logger.warning(f"Skipping already active proxy: {socks5_proxy}")
        return
    active_proxies.add(socks5_proxy)
    user_agent = UserAgent(os=['windows', 'macos', 'linux'], browsers='chrome')
    random_user_agent = user_agent.random
    device_id = str(uuid.uuid3(uuid.NAMESPACE_DNS, socks5_proxy))
    logger.info(f"Device ID: {device_id} for Proxy: {socks5_proxy} with User ID: {user_id}")
    try:
        while True:
            await asyncio.sleep(random.uniform(0.1, 1.0))
            custom_headers = {"User-Agent": random_user_agent}
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            uri = random.choice(WSS_URIS)
            proxy = Proxy.from_url(socks5_proxy)
            async with proxy_connect(uri, proxy=proxy, ssl=ssl_context,
                                     server_hostname=SERVER_HOSTNAME, extra_headers=custom_headers) as websocket:
                async def send_ping():
                    while True:
                        try:
                            send_message = json.dumps(
                                {"id": str(uuid.uuid4()), "version": "1.0.0", "action": "PING", "data": {}}
                            )
                            await websocket.send(send_message)
                            asyncio.create_task(animate_ping_pong("PING"))
                            logger.debug(f"Sending ping: {send_message}")
                            await asyncio.sleep(PING_INTERVAL)
                        except Exception as ping_err:
                            logger.error(f"Ping error: {ping_err}")
                            break
                asyncio.create_task(send_ping())
                while True:
                    response = await websocket.recv()
                    message = json.loads(response)
                    logger.info(f"Received message: {message}")
                    if message.get("action") == "AUTH":
                        auth_response = {
                            "id": message["id"],
                            "origin_action": "AUTH",
                            "result": {
                                "browser_id": device_id,
                                "user_id": user_id,
                                "user_agent": custom_headers['User-Agent'],
                                "timestamp": int(time.time()),
                                "device_type": "desktop",
                                "version": "4.29.0",
                            }
                        }
                        logger.debug(f"Sending AUTH response: {auth_response}")
                        await websocket.send(json.dumps(auth_response))
                    elif message.get("action") == "PONG":
                        asyncio.create_task(animate_ping_pong("PONG"))
                        pong_response = {"id": message["id"], "origin_action": "PONG"}
                        logger.debug(f"Sending PONG response: {pong_response}")
                        await websocket.send(json.dumps(pong_response))
    except Exception as e:
        logger.error(f"Error with proxy {socks5_proxy}: {e}")
        active_proxies.discard(socks5_proxy)
        available_proxies.discard(socks5_proxy)
        logger.info(f"Removed failed proxy: {socks5_proxy}")

async def main():
    global user_ids
    show_banner()
    user_ids = load_user_ids()
    if not user_ids:
        logger.error("No User IDs loaded. Exiting...")
        return
    api_url = select_api_url()
    asyncio.create_task(update_proxies_periodically(api_url))
    while True:
        new_proxies = available_proxies - active_proxies
        tasks = []
        for i, proxy in enumerate(new_proxies):
            user_id = user_ids[i % len(user_ids)]
            tasks.append(asyncio.create_task(connect_to_wss(proxy, user_id)))
        if tasks:
            logger.info(f"Starting {len(tasks)} new connections.")
            await asyncio.gather(*tasks, return_exceptions=True)
        else:
            logger.info("No new proxies to connect. Waiting...")
        await asyncio.sleep(10)

if __name__ == '__main__':
    asyncio.run(main())
