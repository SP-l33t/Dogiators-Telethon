import asyncio
import json
from bot.utils import logger, log_error, AsyncInterProcessLock
from os import path
from copy import deepcopy


def read_config_file(config_path: str) -> dict:
    """Reads the contents of a config file. If the file does not exist, creates it.

     Args:
       config_path: Path to the .json file.

     Returns:
       The contents of the file, or an empty dict if the file was empty or created.
     """
    try:
        with open(config_path, 'r') as f:
            content = f.read()
            config = json.loads(content) if content else {}
    except FileNotFoundError:
        config = {}
        with open(config_path, 'w'):
            logger.warning(f"Accounts config file `{config_path}` not found. Creating a new one.")
    return config


async def write_config_file(content: dict, config_path: str):
    """Writes the contents of a config file. If the file does not exist, creates it.

     Args:
       config_path: Path to the .json file. If empty, 'bot/config/accounts_config.json' is used
       content (dict): Content we want to write

     Returns:
       The contents of the file, or an empty dict if the file was empty or created.
     """
    lock = AsyncInterProcessLock(path.join(path.dirname(config_path), 'lock_files', 'accounts_config.lock'))
    try:
        async with lock:
            with open(config_path, 'w+') as f:
                json.dump(content, f, indent=2)
            await asyncio.sleep(0.1)
    except IOError as e:
        logger.error(f"An error occurred while writing to {config_path}: {e}")


def get_session_config(session_name: str, config_path: str) -> dict:
    """Gets the session config for specified session name.

     Args:
       session_name (dict): The name of the session
       config_path: Path to the .json file. If empty, 'bot/config/accounts_config.json' is used

     Returns:
       The config object for specified session_name, or an empty dict if the file was empty or created.
     """
    return read_config_file(config_path).get(session_name, {})


async def update_session_config_in_file(session_name: str, updated_session_config: dict, config_path: str):
    """Updates the content of a session in config file. If the file does not exist, creates it.

     Args:
       session_name (dict): The name of the session
       updated_session_config (dict): The config to override
       config_path: Path to the .json file. If empty, 'bot/config/accounts_config.json' is used

     Returns:
       The contents of the file, or an empty dict if the file was empty or created.
     """
    try:
        config = read_config_file(config_path)
        config[session_name] = updated_session_config
        await write_config_file(config, config_path)
    except Exception as e:
        log_error(e)


async def restructure_config(config_path: str):
    config = read_config_file(config_path)
    if config:
        cfg_copy = deepcopy(config)
        for key, value in cfg_copy.items():
            api_info = {
                "api_id": value.get('api', {}).get("api_id") or value.pop("api_id", None),
                "api_hash": value.get('api', {}).get("api_hash") or value.pop("api_hash", None),
                "device_model": value.get('api', {}).get("device_model") or value.pop("device_model", None),
                "system_version": value.get('api', {}).get("system_version") or value.pop("system_version", None),
                "app_version": value.get('api', {}).get("app_version") or value.pop("app_version", None),
                "system_lang_code": value.get('api', {}).get("system_lang_code") or value.pop("system_lang_code", None),
                "lang_pack": value.get('api', {}).get("lang_pack") or value.pop("lang_pack", None),
                "lang_code": value.get('api', {}).get("lang_code") or value.pop("lang_code", None)
            }
            api_info = {k: v for k, v in api_info.items() if v is not None}
            cfg_copy[key]['api'] = api_info
        if cfg_copy != config:
            await write_config_file(cfg_copy, config_path)
