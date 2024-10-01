import os

from .logger import logger, log_error
from .async_lock import AsyncInterProcessLock
from . import proxy_utils, config_utils
from bot.config import settings


if not os.path.isdir(settings.GLOBAL_CONFIG_PATH):
    GLOBAL_CONFIG_PATH = os.environ.get(settings.GLOBAL_CONFIG_PATH, "")
else:
    GLOBAL_CONFIG_PATH = settings.GLOBAL_CONFIG_PATH
GLOBAL_CONFIG_EXISTS = os.path.isdir(GLOBAL_CONFIG_PATH)

CONFIG_PATH = os.path.join(GLOBAL_CONFIG_PATH, 'accounts_config.json') if GLOBAL_CONFIG_EXISTS else 'bot/config/accounts_config.json'
SESSIONS_PATH = os.path.join(GLOBAL_CONFIG_PATH, 'sessions') if GLOBAL_CONFIG_EXISTS else 'sessions'
PROXIES_PATH = os.path.join(GLOBAL_CONFIG_PATH, 'proxies.txt') if GLOBAL_CONFIG_EXISTS else 'bot/config/proxies.txt'

PROXY_CHAIN = None
if settings.USE_PROXY_CHAIN:
    path = os.path.join(GLOBAL_CONFIG_PATH, 'proxy_chain.txt')
    PROXY_CHAIN = path if GLOBAL_CONFIG_EXISTS and os.path.isfile(path) else None


if not os.path.exists(path=SESSIONS_PATH):
    os.mkdir(path=SESSIONS_PATH)
