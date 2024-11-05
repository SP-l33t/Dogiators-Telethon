import glob
import asyncio
import argparse
import os
from copy import deepcopy

from bot.utils.universal_telegram_client import UniversalTelegramClient

from bot.config import settings
from bot.core.agents import generate_random_user_agent
from bot.utils import logger, config_utils, proxy_utils, CONFIG_PATH, SESSIONS_PATH, PROXIES_PATH, build_check
from bot.core.tapper import run_tapper
from bot.core.registrator import register_sessions

START_TEXT = """

██████╗░░█████╗░░██████╗░██╗░█████╗░████████╗░█████╗░██████╗░░██████╗
██╔══██╗██╔══██╗██╔════╝░██║██╔══██╗╚══██╔══╝██╔══██╗██╔══██╗██╔════╝
██║░░██║██║░░██║██║░░██╗░██║███████║░░░██║░░░██║░░██║██████╔╝╚█████╗░
██║░░██║██║░░██║██║░░╚██╗██║██╔══██║░░░██║░░░██║░░██║██╔══██╗░╚═══██╗
██████╔╝╚█████╔╝╚██████╔╝██║██║░░██║░░░██║░░░╚█████╔╝██║░░██║██████╔╝
╚═════╝░░╚════╝░░╚═════╝░╚═╝╚═╝░░╚═╝░░░╚═╝░░░░╚════╝░╚═╝░░╚═╝╚═════╝░                                                                                                     
                                                                   
Select an action:

    1. Run clicker
    2. Create session
"""

API_ID = settings.API_ID
API_HASH = settings.API_HASH


def prompt_user_action() -> int:
    logger.info(START_TEXT)
    while True:
        action = input("> ").strip()
        if action.isdigit() and action in ("1", "2"):
            return int(action)
        logger.warning("Invalid action. Please enter 1 or 2.")


async def process() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--action", type=int, help="Action to perform")
    args = parser.parse_args()

    if not settings.USE_PROXY_FROM_FILE:
        logger.info(f"Detected {len(get_sessions(SESSIONS_PATH))} sessions | USE_PROXY_FROM_FILE=False")
    else:
        logger.info(f"Detected {len(get_sessions(SESSIONS_PATH))} sessions | "
                    f"{len(proxy_utils.get_proxies(PROXIES_PATH))} proxies")

    action = args.action or prompt_user_action()

    if action == 1:
        if not API_ID or not API_HASH:
            raise ValueError("API_ID and API_HASH not found in the .env file.")
        await run_tasks()
    elif action == 2:
        await register_sessions()


def get_sessions(sessions_folder: str) -> list[str]:
    session_names = glob.glob(f"{sessions_folder}/*.session")
    session_names += glob.glob(f"{sessions_folder}/telethon/*.session")
    session_names += glob.glob(f"{sessions_folder}/pyrogram/*.session")
    return [file.replace('.session', '') for file in sorted(session_names)]


async def get_tg_clients() -> list[UniversalTelegramClient]:
    session_paths = get_sessions(SESSIONS_PATH)

    if not session_paths:
        raise FileNotFoundError("Session files not found")
    tg_clients = []
    for session in session_paths:
        session_name = os.path.basename(session)
        accounts_config = config_utils.read_config_file(CONFIG_PATH)
        session_config: dict = deepcopy(accounts_config.get(session_name, {}))
        if 'api' not in session_config:
            session_config['api'] = {}
        api_config = session_config.get('api', {})
        api = None
        if api_config.get('api_id') in [4, 6, 2040, 10840, 21724]:
            api = config_utils.get_api(api_config)

        if api:
            client_params = {
                "session": session,
                "api": api
            }
        else:
            client_params = {
                "api_id": api_config.get("api_id", API_ID),
                "api_hash": api_config.get("api_hash", API_HASH),
                "session": session,
                "lang_code": api_config.get("lang_code", "en"),
                "system_lang_code": api_config.get("system_lang_code", "en-US")
            }

            for key in ("device_model", "system_version", "app_version"):
                if api_config.get(key):
                    client_params[key] = api_config[key]

        session_config['user_agent'] = session_config.get('user_agent', generate_random_user_agent())
        api_config.update(api_id=client_params.get('api_id') or client_params.get('api').api_id,
                          api_hash=client_params.get('api_hash') or client_params.get('api').api_hash)

        session_proxy = session_config.get('proxy')
        if not session_proxy and 'proxy' in session_config.keys():
            tg_clients.append(UniversalTelegramClient(**client_params))
            if accounts_config.get(session_name) != session_config:
                await config_utils.update_session_config_in_file(session_name, session_config, CONFIG_PATH)
            continue

        else:
            if settings.DISABLE_PROXY_REPLACE:
                proxy = session_proxy or next(iter(proxy_utils.get_unused_proxies(accounts_config, PROXIES_PATH)), None)
            else:
                proxy = await proxy_utils.get_working_proxy(accounts_config, session_proxy) \
                    if session_proxy or settings.USE_PROXY_FROM_FILE else None

            if not proxy and (settings.USE_PROXY_FROM_FILE or session_proxy):
                logger.warning(f"{session_name} | Didn't find a working unused proxy for session | Skipping")
                continue
            else:
                tg_clients.append(UniversalTelegramClient(**client_params))
                session_config['proxy'] = proxy
                if accounts_config.get(session_name) != session_config:
                    await config_utils.update_session_config_in_file(session_name, session_config, CONFIG_PATH)

    return tg_clients


async def init_config_file():
    session_paths = get_sessions(SESSIONS_PATH)

    if not session_paths:
        raise FileNotFoundError("Session files not found")
    for session in session_paths:
        session_name = os.path.basename(session)
        parsed_json = config_utils.import_session_json(session)
        if parsed_json:
            accounts_config = config_utils.read_config_file(CONFIG_PATH)
            session_config: dict = deepcopy(accounts_config.get(session_name, {}))
            session_config['user_agent'] = session_config.get('user_agent', generate_random_user_agent())
            session_config['api'] = parsed_json
            if accounts_config.get(session_name) != session_config:
                await config_utils.update_session_config_in_file(session_name, session_config, CONFIG_PATH)


async def run_tasks():
    await config_utils.restructure_config(CONFIG_PATH)
    await init_config_file()
    await build_check.check_base_url()
    tg_clients = await get_tg_clients()
    tasks = [asyncio.create_task(run_tapper(tg_client=tg_client)) for tg_client in tg_clients]
    tasks.append(asyncio.create_task(build_check.check_bot_update_loop(2000)))
    await asyncio.gather(*tasks)
