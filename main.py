import asyncio
from contextlib import suppress
from bot.core.launcher import process
from bot.utils import PROXY_CHAIN, logger
from bot.utils.proxy_utils import get_proxy_chain, check_proxy
from os import system


async def main():
    if PROXY_CHAIN:
        proxy_str, proxy = await get_proxy_chain(PROXY_CHAIN)
        if proxy:
            logger.info("Getting proxy for Proxy Chain")
            if await check_proxy(proxy_str):
                import socket, socks
                socks.set_default_proxy(proxy)
                socket.socket = socks.socksocket
            else:
                logger.error("Proxy chain didn't respond. Can't start the bot using proxy chain")
                input('Press any key to exit: ')
                exit(0)
        else:
            logger.warning("No valid proxy found. Skipping")
    await process()


if __name__ == '__main__':
    system('title Dogiators')
    with suppress(KeyboardInterrupt):
        asyncio.run(main())
