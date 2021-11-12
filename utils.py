import codecs
import json
import os

import requests
from loguru import logger

USER_AGENTS = [
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:90.0) Gecko/20100101 Firefox/90.0',
    'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.101 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.106 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36 Edg/91.0.864.59',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36 OPR/77.0.4054.172',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.64',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.67',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.70',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 OPR/77.0.4054.203',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.164 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.164 Safari/537.36 Edg/91.0.864.71',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36 Edg/92.0.902.55'
]


class DataJsonException(Exception):
    pass


def load_data_from_file():
    try:
        if not os.path.exists('data.json'):
            with codecs.open('data.json', 'w', 'utf-8') as f:
                data = {
                    "telegram": {
                        "bot_token": "",
                        "telegram_id": "",
                        "info_mod": True,
                        "error_mod": True,
                    },
                    "user-agents": [],
                    "proxy": {
                        "account_proxy": "",
                        "proxy_type": "socks5"
                    }
                }
                f.write(json.dumps(data, indent=4))
            logger.info('Edit data.json')
            exit()

        with codecs.open('data.json', 'r', 'utf-8') as f:
            data = f.read()
            data = json.loads(data)
    except json.decoder.JSONDecodeError as error:
        logger.error('Невалид data.json')
        logger.error(error)
        raise DataJsonException('Невалид data.json')

    except KeyError as error:
        logger.error(error)
        logger.error('Cannot find: %s', error.args[0])
    else:
        return data


DATA_JSON = load_data_from_file()
BOT_TOKEN = DATA_JSON.get('telegram').get('bot_token')


def telegram_bot_send_text(bot_message, telegram_id, is_silent=False):
    bot_token = BOT_TOKEN

    url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
    data = {
        'chat_id': telegram_id,
        'text': bot_message,
        'parse_mode': 'html'
    }

    if is_silent:
        data['disable_notification'] = 'true'

    try:
        response = requests.get(url, data=data)
        logger.info(str(response.json()))
    except Exception as e:
        logger.error('Fail to send telegram message')


def get_data_from_proxy(account_proxy):
    host = account_proxy.split('@')[1]
    user = account_proxy.split('@')[0]
    http_proxy_host = host.split(':')[0]
    http_proxy_port = host.split(':')[1]
    http_proxy_auth = (
        user.split(':')[0],
        user.split(':')[1]
    )
    return http_proxy_host, http_proxy_port, http_proxy_auth
