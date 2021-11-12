import base64
import json
import os
import random
import re
import ssl
import sys
import time
import traceback
from threading import Event, Thread

import requests
import websocket
from bs4 import BeautifulSoup
from loguru import logger
from requests import RequestException

from config import domain_name
from utils import load_data_from_file, get_data_from_proxy, telegram_bot_send_text, USER_AGENTS

DATA_JSON = load_data_from_file()


class CookieException(Exception):
    pass


class ProxySetError(Exception):
    pass


class LolzWorker:
    def __init__(self, data_user):
        """
        Constructor.
        """
        self.user_data: dict = data_user
        self.website_shit = 0
        self.session = requests.Session()
        user_agent = data_user.get('user-agents')

        if user_agent:
            if len(user_agent) > 0:
                self.session.headers.update({'User-Agent': random.choice(user_agent)})
        else:
            self.session.headers.update({'User-Agent': random.choice(USER_AGENTS)})
        self.data = {'_xfResponseType': 'json'}
        self.domain_name: str = domain_name

        self.is_proxy: bool = False
        self.ws = websocket.WebSocket(sslopt={"cert_reqs": ssl.CERT_NONE})
        self.telegram_id = ''

        if self.user_data['telegram']['telegram_id'] != '':
            self.telegram_id: int = self.user_data['telegram']['telegram_id']
            self.is_info_mod: bool = self.user_data['telegram']['info_mod']
            self.is_error_mode: bool = self.user_data['telegram']['error_mod']
        else:
            self.is_error_mode: bool = False
            self.is_info_mod: bool = False

        if self.user_data['proxy']['account_proxy'] != '':
            self.account_proxy: str = self.user_data['proxy']['account_proxy']
            self.proxy_type: str = self.user_data['proxy']['proxy_type']
            self.is_proxy: bool = True
            logger.info(self.account_proxy)
            if not self.proxy_check():
                logger.error('Proxy set error')
                if self.is_error_mode:
                    telegram_bot_send_text('Proxy set error', is_silent=False, telegram_id=self.telegram_id)
                raise ProxySetError('Proxy set error. Вид прокси \"user:pass@ip:port\" ipv4')

        if not os.path.isfile('cookie.txt'):
            with open('cookie.txt', 'w') as f:
                f.write('')
            sys.exit('Заполни куки')
        else:
            self.cookie_load()
        self.username = None
        self.token = None
        self.session.cookies['xf_logged_in'] = '1'
        self.session.cookies['xf_is_mobile'] = '1'

        if self.is_proxy:
            self.http_proxy_host, self.http_proxy_port, self.http_proxy_auth = get_data_from_proxy(self.account_proxy)
        self.set_df_id()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        message = str(traceback.format_exc())
        logger.error(message)
        if self.is_error_mode:
            telegram_bot_send_text(message, is_silent=False, telegram_id=self.telegram_id)

    def proxy_check(self) -> bool:
        if 'http' in self.proxy_type:
            self.proxy_type = 'http'

        proxy: dict = {
            'http': f"{self.proxy_type}://{self.account_proxy}",
            'https': f"{self.proxy_type}://{self.account_proxy}",
        }
        api_urls = [
            'https://api.ipify.org?format=json',
            'https://ip.seeip.org/jsonip?',
            'https://ipwhois.app/json/',
            'https://l2.io/ip.json',
            'https://api.myip.co',
        ]
        try:
            self.session.proxies.update(proxy)
            for link in api_urls:
                try:
                    response_no_proxy = requests.get(link, timeout=5).json()
                    response_with_proxy = self.session.get(link, timeout=5).json()

                    logger.info(f'Your ip: {response_no_proxy}')
                    logger.info(f'Ip with proxy: {response_with_proxy}')

                    if response_with_proxy['ip'] == response_no_proxy['ip']:
                        return False
                    else:
                        return True
                except Exception as e:
                    logger.error(e)
        except Exception as error:
            logger.error(error)
            logger.error('Proxy set error!')
            if self.is_error_mode:
                telegram_bot_send_text(f'Proxy set error!\n{error}', is_silent=False, telegram_id=self.telegram_id)
            sys.exit('Proxy set error!')

    def is_login(self) -> bool:
        """
        Check is user login
        :return:
        """
        try:
            response = self.session.get(f'https://{self.domain_name}/')
            if response.status_code != 200:
                logger.error('Check website')
                time.sleep(10)
                return False
            req_bs = BeautifulSoup(response.text, 'lxml')
            logger.info(str(req_bs.select_one('img[class="navTab--visitorAvatar"]')))
            if req_bs.select_one('script[src="/process-qv9ypsgmv9.js"]'):
                logger.info(response.text)
                return False
            if not req_bs.select_one('img[class="navTab--visitorAvatar"]'):
                return False
            return True
        except Exception as error:
            logger.error(error)
            return False

    def get_xftoken(self) -> str:
        """
        Parse page and get xfToken
        :return:
        """
        try:
            response = self.session.get(f'https://{self.domain_name}/')
            token_bs = BeautifulSoup(response.content, 'lxml')
            token = token_bs.find('input', {'name': '_xfToken'})['value']
            self.username = token_bs.select_one('a[class="username"]').span.text.strip()
            self.token = token
            logger.info(f'Get xftoken: {token}')
        except RequestException as e:
            if self.is_error_mode:
                telegram_bot_send_text(str(e), telegram_id=self.telegram_id)
            logger.error(e)
            raise e
        else:
            return token

    def cookie_load(self):
        with open('cookie.txt') as file:
            try:
                cookies_lines = json.load(file)
                for line in cookies_lines:
                    if 'name' in line:
                        self.session.cookies[line.get('name')] = line.get('value')

                for line in cookies_lines:
                    if ('name' or 'value' or 'hostOnly' or 'domain') in line:
                        break
                    self.session.cookies[line] = cookies_lines[line]
            except (UnicodeDecodeError, json.JSONDecodeError) as e:
                logger.error(e)
                logger.error('Не смог загрузить куки')
                raise CookieException('Не смог загрузить куки')

    @staticmethod
    def read_socket_message(message):
        """
        Get message type from binary data
        :return:
        """
        try:
            type_ = re.search(r'\d+', message).group(0)
            message_ = message[len(type_):]
            type_ = int(type_)
        except Exception as error:
            logger.error(error)
            return None, None
        else:
            return type_, message_

    def call_repeatedly(self, interval):
        stopped = Event()

        def loop():
            while not stopped.wait(interval):  # the first call is in `interval` secs
                self.ws.send('2')
                logger.info('Keep alive')

        Thread(target=loop).start()
        return stopped.set

    async def get_balance(self) -> int:
        try:
            response = self.session.get('https://lolz.guru/market/')
            bs = BeautifulSoup(response.content, 'lxml')
        except RequestException as e:
            logger.error(e)
            return 0

        try:
            balance = bs.select_one('span[class="balanceValue"]').text
            return balance.strip()
        except AttributeError as error:
            logger.error(error)
            return 0

    def send_message(self, message):
        try:
            data = {
                'message': message,
                '_xfRequestUri': '/chatbox/',
                '_xfNoRedirect': 1,
                '_xfToken': self.token,
                '_xfResponseType': 'json'
            }
            response = self.session.post('https://lolz.guru/index.php?chatbox/post-message', data=data).json()
            logger.info(response)
            if 'templateHtml' in response:
                return True
            else:
                return False
        except Exception as e:
            logger.error(e)
            telegram_bot_send_text(e, self.telegram_id)

    @staticmethod
    def get_chat_message(message):
        try:
            json_mes = json.loads(message)[1].get('templateHtml')
            soup = BeautifulSoup(json_mes, 'lxml')
            profile_url = soup.select_one('a[class="username"]').get('href')
            username = soup.select_one('a[class="username"]').span.text
            a_url = f'<a href="https://lolz.guru/{profile_url}"><strong>{username}</strong></a>'
            text_html = soup.select_one('div[class="messageContent"]')
            text = text_html.text.strip() + ' '
            for smile in text_html.select('img[alt]'):
                text += smile.get('alt') + ' '
            message_send = f'{a_url} : {text}'
            return message_send
        except (json.JSONDecodeError, AttributeError) as e:
            logger.error(e)
            return None

    def socket(self, data_id):
        url = 'wss://ws.lolz.guru:3000/socket.io/?EIO=3&transport=websocket'
        headers = {
            'User-Agent': random.choice(USER_AGENTS),
        }

        if self.is_proxy:
            self.ws.connect(
                url,
                http_proxy_host=self.http_proxy_host,
                http_proxy_port=self.http_proxy_port,
                proxy_type=self.proxy_type,
                http_proxy_auth=self.http_proxy_auth,
                header=headers
            )
        else:
            self.ws.connect(url, header=headers)
        is_inited = False
        try:
            while True:
                data = self.ws.recv()
                message_type, message = self.read_socket_message(data)
                logger.debug(f'{message_type}: {message}')

                if message_type == 42 and 'newMessage' in message:
                    message_send = self.get_chat_message(message)
                    logger.info(message_send)
                    if self.is_info_mod:
                        telegram_bot_send_text(message_send, telegram_id=self.telegram_id, is_silent=False)
                elif message_type == 42 and 'retrieveInfos' in message:
                    self.ws.send(f'42["retrieveInfos","{data_id}"]')
                    logger.info('Send data_id')
                    self.call_repeatedly(25)
                    is_inited = True
                if is_inited:
                    time.sleep(1)

        except Exception as error:
            logger.error(error)
            return False
        finally:
            self.ws.close()

    @staticmethod
    async def check_notifications(soup):
        notifications = soup.select_one('div[id="AlertsMenu_Counter"]')
        notifications = notifications.select_one('span[class="Total"]').text
        if notifications != '0':
            return True
        else:
            return False

    async def get_new_notifications(self):
        try:
            response = self.session.get('https://lolz.guru/')
        except RequestException as error:
            logger.info(error)
            return False
        soup = BeautifulSoup(response.content, 'lxml')
        res = await self.check_notifications(soup)
        if not res:
            return False
        try:
            response = self.session.get('https://lolz.guru/account/alerts')
        except RequestException as error:
            logger.info(error)
            return False
        soup = BeautifulSoup(response.content, 'lxml')
        list_notifications = soup.select_one('ol[class="alerts alertsScroller"]')

        notifications_dict = {}
        for i, item in enumerate(list_notifications.select('li[class="primaryContent listItem Alert new unviewed"]')):
            print(item.select_one('h3').text)
            try:
                text = item.select_one('h3').text
                username = item.select_one('a[class="username"]').text
                user_link = f'https://{self.domain_name}/' + item.select_one('a[class="username"]').get('href')
                post_link = f'https://{self.domain_name}/' + item.select_one('a[class="PopupItemLink"]').get('href')
                post_link_text = item.select_one('a[class="PopupItemLink"]').text
                time = item.select_one('span[class="time muted"]').text
                notifications_dict[i] = {
                    'text': text,
                    'username': username,
                    'user_link': user_link,
                    'post_link': post_link,
                    'post_link_text': post_link_text,
                    'time': time
                }
            except AttributeError as error:
                logger.error(error)
                continue
        return notifications_dict

    def participate_in_contests(self):
        self.token = self.get_xftoken()
        while True:
            try:
                response = self.session.get('https://lolz.guru/chatbox/')
                soup = BeautifulSoup(response.content, 'lxml')
                data_id = soup.select_one('div[id="chatbox"]').get('data-id')
                self.socket(data_id)
            except Exception as e:
                logger.error(e)

    def set_df_id(self) -> None:
        """
        Get and set df_id cookie
        :return: None
        """
        try:
            response_text = self.session.get(f"https://{self.domain_name}/process-qv9ypsgmv9.js").text
            df_id = base64.b64decode(
                re.sub(
                    r"'\+'", "",
                    re.search(
                        r"var _0x2ef7=\[[A-Za-z0-9+/=',]*','([A-Za-z0-9+/=']*?)'];",
                        response_text).group(1)
                )
            )
            self.session.cookies['df_id'] = df_id.decode('ascii')
        except (RequestException, IndexError) as error:
            logger.error('IP BAN, maybe.')
            if self.is_error_mode:
                telegram_bot_send_text(str(error), telegram_id=self.telegram_id)
            logger.error(error)
