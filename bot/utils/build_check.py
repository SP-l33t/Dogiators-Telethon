import asyncio
import re
import aiohttp
import sys
import json
from random import uniform
from bot.utils import logger
from bot.config import settings
from hashlib import sha256

appUrl = "https://tte.dogiators.com"
versions = "https://github.com/SP-l33t/Auxiliary-Data/raw/refs/heads/main/version_track.json"

headers = {
    'accept': '*/*',
    'user-agent': 'Mozilla/5.0 (Linux; Android 7.1.2; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.6045.193 Mobile Safari/537.36'
}


async def get_main_js_format(base_url):
    async with aiohttp.request(url=base_url, method="GET", headers=headers) as response:
        response.raise_for_status()
        try:
            content = await response.text()
            matches = re.findall(r'src="(/.*?\.js)"', content)
            return sorted(set(matches), key=len, reverse=True) if matches else None
        except Exception as e:
            logger.warning(f"Error fetching the base URL: {e}")
            return None


async def get_versions(service):
    async with aiohttp.request(url=versions, method="GET") as response:
        if response.status in range(200, 300):
            return json.loads(await response.text()).get(service, {})


async def get_js_hash(path):
    async with aiohttp.request(url=appUrl+path, method="GET", headers=headers) as response:
        if response.status in range(200, 300):
            return sha256((await response.text()).encode('utf-8')).hexdigest()


async def check_base_url():
    if settings.TRACK_BOT_UPDATES:
        main_js_formats = await get_main_js_format(appUrl)
        if main_js_formats:
            last_actual_files = await get_versions('dogiators')
            last_actual_js = last_actual_files.get('main_js')
            last_actual_hash = last_actual_files.get('js_hash')
            for js in main_js_formats:
                if last_actual_js in js:
                    live_hash = await get_js_hash(js)
                    if live_hash == last_actual_hash:
                        logger.success(f"No changes in main js file: <green>{last_actual_js}</green>")
                        return True
                else:
                    logger.error(f"Main JS updated. New file name: <lr>'{js}'</lr>. "
                                 f"Hash: '<lr>{await get_js_hash(js)}</lr>'. Old hash: <lg>{last_actual_hash}</lg>")
                    sys.exit("Bot updates detected. Contact me to check if it's safe to continue: https://t.me/SP_l33t")

        else:
            logger.error("<lr>No main js file found. Can't continue</lr>")
            sys.exit("No main js file found. Contact me to check if it's safe to continue: https://t.me/SP_l33t")


async def check_bot_update_loop(start_delay: 0):
    await asyncio.sleep(start_delay)
    while settings.TRACK_BOT_UPDATES:
        await check_base_url()
        await asyncio.sleep(uniform(1500, 2000))
