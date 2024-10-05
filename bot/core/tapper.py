import aiohttp
import asyncio
import os
import random
from urllib.parse import unquote, quote
from aiocfscrape import CloudflareScraper
from aiohttp_proxy import ProxyConnector
from better_proxy import Proxy
from datetime import datetime, timedelta
from time import time

from telethon import TelegramClient
from telethon.errors import *
from telethon.types import InputBotAppShortName, InputNotifyPeer, InputPeerNotifySettings, InputUser
from telethon.functions import messages, account, channels

from bot.config import settings
from bot.utils import logger, log_error, proxy_utils, config_utils, AsyncInterProcessLock, CONFIG_PATH
from bot.exceptions import InvalidSession
from .headers import headers, get_sec_ch_ua

API_ENDPOINT = "https://tte.dogiators.com/api/v1"


class Tapper:
    def __init__(self, tg_client: TelegramClient):
        self.tg_client = tg_client
        self.session_name, _ = os.path.splitext(os.path.basename(tg_client.session.filename))
        self.lock = AsyncInterProcessLock(
            os.path.join(os.path.dirname(CONFIG_PATH), 'lock_files', f"{self.session_name}.lock"))
        self.headers = headers

        session_config = config_utils.get_session_config(self.session_name, CONFIG_PATH)

        if not all(key in session_config for key in ('api_id', 'api_hash', 'user_agent')):
            logger.critical(self.log_message('CHECK accounts_config.json as it might be corrupted'))
            exit(-1)

        user_agent = session_config.get('user_agent')
        self.headers['user-agent'] = user_agent
        self.headers.update(**get_sec_ch_ua(user_agent))

        self.proxy = session_config.get('proxy')
        if self.proxy:
            proxy = Proxy.from_str(self.proxy)
            proxy_dict = proxy_utils.to_telethon_proxy(proxy)
            self.tg_client.set_proxy(proxy_dict)

        self.ref_code = None
        self.tg_web_data = None

        self._webview_data = None

    def log_message(self, message) -> str:
        return f"<ly>{self.session_name}</ly> | {message}"

    async def initialize_webview_data(self):
        if not self._webview_data:
            while True:
                try:
                    peer = await self.tg_client.get_input_entity('Dogiators_bot')
                    bot_id = InputUser(user_id=peer.user_id, access_hash=peer.access_hash)
                    input_bot_app = InputBotAppShortName(bot_id=bot_id, short_name="game")
                    self._webview_data = {'peer': peer, 'app': input_bot_app}
                    break
                except FloodWaitError as fl:
                    logger.warning(self.log_message(f"FloodWait {fl}. Waiting {fl.seconds}s"))
                    await asyncio.sleep(fl.seconds + 3)
                except (UnauthorizedError, AuthKeyUnregisteredError):
                    raise InvalidSession(f"{self.session_name}: User is unauthorized")
                except (UserDeactivatedError, UserDeactivatedBanError, PhoneNumberBannedError):
                    raise InvalidSession(f"{self.session_name}: User is banned")

    async def get_tg_web_data(self):
        if self.proxy and not self.tg_client._proxy:
            logger.critical(self.log_message('Proxy found, but not passed to TelegramClient'))
            exit(-1)
        async with self.lock:
            try:
                if not self.tg_client.is_connected():
                    await self.tg_client.connect()
                await self.initialize_webview_data()
                await asyncio.sleep(random.uniform(1, 2))

                ref_id = settings.REF_ID if random.randint(0, 100) <= 85 else "s5XexnShM18Ftejz"

                web_view = await self.tg_client(messages.RequestAppWebViewRequest(
                    **self._webview_data,
                    platform='android',
                    write_allowed=True,
                    start_param=ref_id
                ))

                auth_url = web_view.url
                tg_web_data = quote(unquote(string=auth_url.split('tgWebAppData=')[1].split('&tgWebAppVersion')[0]))

                self.tg_web_data = f"tg_data={tg_web_data}"
                self.ref_code = f'&referral_code={ref_id}' if ref_id else ""

            except InvalidSession:
                raise

            except Exception as error:
                log_error(self.log_message(f"Unknown error during Authorization: {type(error).__name__}"))
                await asyncio.sleep(delay=3)

            finally:
                if self.tg_client.is_connected():
                    await self.tg_client.disconnect()
                    await asyncio.sleep(15)

        return self.tg_web_data

    async def join_and_mute_tg_channel(self, link: str):
        path = link.replace("https://t.me/", "")
        if path == 'money':
            return

        async with self.lock:
            async with self.tg_client as client:
                try:
                    if path.startswith('+'):
                        invite_hash = path[1:]
                        result = await client(messages.ImportChatInviteRequest(hash=invite_hash))
                        channel_title = result.chats[0].title
                        entity = result.chats[0]
                    else:
                        entity = await client.get_entity(f'@{path}')
                        await client(channels.JoinChannelRequest(channel=entity))
                        channel_title = entity.title

                    await asyncio.sleep(1)

                    await client(account.UpdateNotifySettingsRequest(
                        peer=InputNotifyPeer(entity),
                        settings=InputPeerNotifySettings(
                            show_previews=False,
                            silent=True,
                            mute_until=datetime.today() + timedelta(days=365)
                        )
                    ))

                    logger.info(self.log_message(f"Subscribe to channel: <y>{channel_title}</y>"))
                except Exception as e:
                    log_error(self.log_message(f"(Task) Error while subscribing to tg channel: {e}"))

            await asyncio.sleep(15)

    async def check_proxy(self, http_client: aiohttp.ClientSession) -> bool:
        proxy_conn = http_client.connector
        if proxy_conn and not hasattr(proxy_conn, '_proxy_host'):
            logger.info(self.log_message(f"Running Proxy-less"))
            return True
        try:
            response = await http_client.get(url='https://ifconfig.me/ip', timeout=aiohttp.ClientTimeout(15))
            logger.info(self.log_message(f"Proxy IP: {await response.text()}"))
            return True
        except Exception as error:
            proxy_url = f"{proxy_conn._proxy_type}://{proxy_conn._proxy_host}:{proxy_conn._proxy_port}"
            log_error(self.log_message(f"Proxy: {proxy_url} | Error: {type(error).__name__}"))
            return False

    @staticmethod
    async def get_time_zone(http_client: aiohttp.ClientSession):
        try:
            resp = await http_client.get("http://ip-api.com/json/")
            return (await resp.json())['timezone']
        except:
            return "Europe/Berlin"

    async def get_quests(self, http_client: aiohttp.ClientSession):
        await asyncio.sleep(random.uniform(1, 3))
        response = await http_client.get(url=f"{API_ENDPOINT}/quests/info?{self.tg_web_data}{self.ref_code}")
        if response.status == 200:
            quests_json = await response.json()
            if quests_json.get('status', False):
                return quests_json.get('result')
        else:
            logger.warning(self.log_message(f"Failed to get Quests: {response.status}: {await response.text()}</red>"))
            return None

    async def get_user_profile(self, http_client: aiohttp.ClientSession, time_zone: str):
        await asyncio.sleep(random.uniform(1, 3))
        response = await http_client.post(f'{API_ENDPOINT}/profile/init?{self.tg_web_data}{self.ref_code}',
                                          json={"taps": 0, "profit": 0, "ts": 0, "timezone": time_zone})
        if response.status == 200:
            json_data = await response.json()
            profile = json_data.get('result', {}).get('profile')
            if profile:
                return profile
            else:
                return None

    async def send_taps(self, http_client: aiohttp.ClientSession, profile: dict):
        await asyncio.sleep(random.uniform(5, 10))
        curr_energy = profile.get('cur_energy', 0)
        profit_per_tap = profile.get('profit_per_tap', 10)
        taps = int(curr_energy / profit_per_tap * random.uniform(0.75, 0.85))
        profit = max(curr_energy - curr_energy % profit_per_tap - random.randint(1, 20) * 10, 0)
        http_client.headers['content-type'] = "application/json"
        response = await http_client.patch(f"{API_ENDPOINT}/profile/update?{self.tg_web_data}{self.ref_code}",
                                           json={"taps": taps,
                                                 "profit": profit,
                                                 "timestamp": int(time())})
        http_client.headers.pop('content-type', "")
        if response.status == 200:
            resp_json = await response.json()
            if resp_json.get('status', False):
                logger.success(
                    self.log_message(f"Successfully tapped <lc>{taps}</lc> times and got <lc>{profit}</lc> coins"))
                return resp_json.get('result', {}).get('profile')

        return None

    async def spin_wheel_of_fortune(self, http_client: aiohttp.ClientSession):
        await asyncio.sleep(random.uniform(2, 5))
        get_spin_prizes = await http_client.get(url=f"{API_ENDPOINT}/fortune/info?{self.tg_web_data}{self.ref_code}")
        if get_spin_prizes.status != 200:
            logger.error(self.log_message(F"Failed to spin the wheel. Code: {get_spin_prizes.status}"))
            return

        spin_result = await http_client.post(
            url=f"{API_ENDPOINT}/fortune/simple-wheel/run?{self.tg_web_data}{self.ref_code}")
        if spin_result.status != 200:
            logger.error(self.log_message(F"Failed to spin the wheel. Code: {get_spin_prizes.status}"))
            return

        spin_result_json = await spin_result.json()
        if spin_result_json.get('status', False):
            spin_result_json = spin_result_json.get('result')
            logger.success(self.log_message(
                f"Spin successfully. Won: <lc>{spin_result_json.get('value')} {spin_result_json.get('type')}</lc>"))
            return True

        return

    async def perform_daily_checkin(self, http_client: aiohttp.ClientSession):
        await asyncio.sleep(random.uniform(2, 5))
        daily_reward = await http_client.post(
            url=f"{API_ENDPOINT}/quests/daily-reward/claim?{self.tg_web_data}{self.ref_code}")
        if daily_reward.status == 200 and (await daily_reward.json()).get('status', False):
            return True

        return

    async def perform_subscribe_quest(self, http_client: aiohttp.ClientSession, quest: dict):
        if quest.get('type', "") in ["verify:ton_wallet_verify", "verify:ton_transaction_completed",
                                     'perform:single_fight']:
            return

        if quest.get('type', "") == "subscribe:telegram" and settings.CHANNEL_SUBSCRIBE_TASKS:
            if quest.get('link'):
                await self.join_and_mute_tg_channel(quest.get('link'))
                await asyncio.sleep(random.uniform(15, 20))
        elif quest.get('type', "") == "subscribe:telegram" and not settings.CHANNEL_SUBSCRIBE_TASKS:
            return
        await asyncio.sleep(random.uniform(2, 5))
        quest_reward = await http_client.post(
            url=f"{API_ENDPOINT}/quests/subscribe/claim?{self.tg_web_data}{self.ref_code}",
            json={"type": quest.get('type')})
        if quest_reward.status == 200:
            reward_json = await quest_reward.json()
            profit = reward_json.get('result', {}).get('profit')
            if profit:
                logger.success(self.log_message(f"Successfully completed quest <lc>{quest.get('type')}</lc> "
                                                f"and got <lc>{profit}</lc> coins"))
                return True

        return

    async def get_upgrades_list(self, http_client: aiohttp.ClientSession):
        await asyncio.sleep(random.uniform(2, 5))
        response = await http_client.get(f"{API_ENDPOINT}/upgrade/list?{self.tg_web_data}{self.ref_code}")
        if response.status == 200:
            resp_json = await response.json()
            if resp_json.get('status', False):
                return resp_json.get('result', {})
        else:
            logger.error(
                self.log_message(f"Failed to grab list of upgrades. {response.status}. {await response.text()}"))
            return {}

    async def upgrade_card(self, http_client: aiohttp.ClientSession, upgrade_id: int) -> bool:
        await asyncio.sleep(random.uniform(1, 3))
        response = await http_client.post(f"{API_ENDPOINT}/upgrade/buy?{self.tg_web_data}{self.ref_code}",
                                          json={"upgrade_id": upgrade_id})
        if response.status == 200:
            resp_json = await response.json()
            if resp_json.get('status', False):
                return True
        return False

    @staticmethod
    async def select_best_upgrade(json_object, available_money):
        upgrades = json_object['system_upgrades'] + json_object['special_upgrades']
        profile_upgrades = json_object['profile_upgrades']

        # Convert profile upgrades to a dictionary for easy lookup
        profile_upgrades_dict = {upgrade['upgrade_id']: upgrade['level'] for upgrade in profile_upgrades}

        best_upgrade_id = None
        upgrade_title = None
        best_efficiency = 0

        for upgrade in upgrades:
            current_level = profile_upgrades_dict.get(upgrade['id'], 0)
            if current_level >= len(upgrade['modifiers']):
                continue  # No more levels to upgrade

            next_modifier = upgrade['modifiers'][current_level]
            price = next_modifier['price']
            profit_relative = next_modifier['profit_per_hour_relative']

            if price > available_money:
                continue

            # Check requirements
            can_upgrade = True
            for requirement in upgrade.get('requirements', []):
                if (requirement['reach_upgrade_level'] > profile_upgrades_dict.get(requirement['reach_upgrade_id'], 0)
                        or requirement['min_referrals_count'] > 0):
                    can_upgrade = False
                    break

            if not can_upgrade:
                continue

            efficiency = profit_relative / price
            if efficiency > best_efficiency:
                best_efficiency = efficiency
                best_upgrade_id = upgrade['id']
                upgrade_title = upgrade['title']

        return best_upgrade_id, upgrade_title

    async def run(self) -> None:
        random_delay = random.uniform(1, settings.RANDOM_SESSION_START_DELAY)
        logger.info(self.log_message(f"Bot will start in <light-red>{int(random_delay)}s</light-red>"))
        await asyncio.sleep(delay=random_delay)

        access_token_created_time = 0
        tg_web_data = None
        profile = None

        proxy_conn = {'connector': ProxyConnector.from_url(self.proxy)} if self.proxy else {}
        async with CloudflareScraper(headers=self.headers, timeout=aiohttp.ClientTimeout(60),
                                     **proxy_conn) as http_client:
            time_zone = await self.get_time_zone(http_client)
            while True:
                if not await self.check_proxy(http_client=http_client):
                    logger.warning(self.log_message('Failed to connect to proxy server. Sleep 5 minutes.'))
                    await asyncio.sleep(300)
                    continue
                token_live_time = random.randint(3500, 3600)
                try:
                    if time() - access_token_created_time >= token_live_time or not tg_web_data:
                        tg_web_data = await self.get_tg_web_data()

                        if not tg_web_data:
                            logger.warning(self.log_message('Failed to get webview URL'))
                            await asyncio.sleep(300)
                            continue

                        access_token_created_time = time()

                    profile = await self.get_user_profile(http_client, time_zone)
                    if profile:
                        logger.success(self.log_message(f"Balance <lc>{int(profile['balance'])}</lc> "
                                                        f"Level <lc>{profile['level']}</lc> "
                                                        f"Profit per hour <lc>{profile['profit_per_hour']}</lc> "
                                                        f"Spins <lc>{profile['lottery_tickets']}</lc>"))
                    else:
                        logger.error(self.log_message(f"Failed to get profile data. Sleep 5 minutes"))
                        await asyncio.sleep(300)
                        continue

                    if settings.AUTO_TAP:
                        profile = await self.send_taps(http_client, profile)
                        if not profile:
                            logger.error(self.log_message("Failed to send taps. Sleep 5 minutes"))

                    if settings.SPIN_THE_WHEEL:
                        tickets = profile.get('lottery_tickets', 0)
                        for i in range(tickets):
                            await self.spin_wheel_of_fortune(http_client)

                    quests = await self.get_quests(http_client)

                    if settings.PERFORM_QUESTS:
                        daily = quests.get('daily_rewards', {}).get('reward_days', {})
                        subscribe = quests.get('subscriptions_state', {})
                        for day in daily:
                            if day.get('is_current', False):
                                if not day.get('is_completed', True):
                                    daily_result = await self.perform_daily_checkin(http_client)
                                    if daily_result:
                                        logger.success(self.log_message(f"Successfully claimed daily reward: "
                                                                        f"<lc>{day.get('value')}</lc> coins"))
                                    else:
                                        logger.warning(self.log_message("Failed to claim daily reward"))
                                break

                        for task in subscribe:
                            if not task.get('is_completed', False):
                                await self.perform_subscribe_quest(http_client, task)

                    if settings.UPGRADE_CARDS:
                        can_upgrade = True
                        while can_upgrade:
                            profile = await self.get_user_profile(http_client, time_zone)
                            upgrades_list = await self.get_upgrades_list(http_client)
                            balance = profile.get('balance', 0)
                            get_upgrade_id, get_upgrade_title = await self.select_best_upgrade(upgrades_list, balance)
                            if get_upgrade_id:
                                upgrade_result = await self.upgrade_card(http_client, get_upgrade_id)
                                if upgrade_result:
                                    logger.success(
                                        self.log_message(f"Successfully upgraded <lc>{get_upgrade_title}</lc>"))
                                else:
                                    logger.error(self.log_message(f"Failed to upgrade <lc>{get_upgrade_title}</lc>"))
                            else:
                                can_upgrade = False

                    sleep_time = random.randint(settings.RANDOM_SLEEP_TIME[0], settings.RANDOM_SLEEP_TIME[1])
                    logger.info(self.log_message(f"Balance <lc>{int(profile['balance'])}</lc> "
                                                 f"Level <lc>{profile['level']}</lc> "
                                                 f"Profit per hour <lc>{profile['profit_per_hour']}</lc> "
                                                 f"Spins <lc>{profile['lottery_tickets']}</lc>"))
                    logger.info(self.log_message(f"Completed cycle. waiting {sleep_time} seconds..."))
                    await asyncio.sleep(delay=sleep_time)

                except InvalidSession as error:
                    raise error

                except Exception as error:
                    sleep_time = random.randint(60, 120)
                    log_error(self.log_message(f"Unknown error: {error}. Sleep {sleep_time} seconds"))
                    await asyncio.sleep(delay=sleep_time)


async def run_tapper(tg_client: TelegramClient):
    runner = Tapper(tg_client=tg_client)
    try:
        await runner.run()
    except InvalidSession as e:
        logger.error(runner.log_message(f"Invalid Session: {e}"))
