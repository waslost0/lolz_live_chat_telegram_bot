# lolz_live_chat_telegram_bot
Lolz Live chat telegram bot / Lolz лайв чат в телеграм боте

<img src="https://i.imgur.com/9i8EX9V.png" alt="image" height="700"></img>

## Requirements
- Python 3.8
- Бот в телеграм

## Настройка
### Установка
```shell
git clone https://github.com/waslost0/lolz_live_chat_telegram_bot
cd lolz_live_chat_telegram_bot
pip instal -r requirements.txt
```

Или скачиваем репозиторий, в папке запускаем install_libs.bat

---
### Куки лолза
1) Скачать расширение [EditThisCookie](https://chrome.google.com/webstore/detail/editthiscookie/fngmhnnpilhplaeedifhccceomclgfbg?hl=ru)
2) Перейти на вкладку лолза
3) Экспортировать куки
4) Вставить в файл cookie.txt (создать, если нет)

<img src="https://i.imgur.com/0xmoMRo.png" alt="image">


---
### Настройка конфига
- Запустить `main.py` или `run.bat`, чтобы появился `data.json`

### data.json
|Параметр      |Значения                                     |Обязателен к заполнению| 
|--------------|---------------------------------------------|-----------------------|
| bot_token    |токен бота тг                                | **Да**                |
|telegram_id   | id тг, можно взять в @userinfobot           | **Да**                |
|info_mode     | вкл/выкл чата                               | -                     |
|error_mode    | информация об ошибках                       | -                     |
|account_proxy | прокси ipv4 для лолза вида user:pass@ip:port| Нет                   |
|proxy_type    | тип прокси                                  | Нет                   | 
|user-agents   | юзер агенты                                 | Нет                   |

---
### Телегам бот
1) Пишем в тг боту [@BotFather](https://t.me/botfather)
2) **/newbot**
3) Вводим любое имя бота
4) Вводим username для бота, в конце должно быть **bot**
5) Копируем токен бота, вставляем в data.json в раздел "telegram" ```"bot_token": "ТУТТОКЕН"```
6) Переходим в вашего бота, запускаем его
---
## Запуск
Запустить можно с помощью файла **run.bat** или с консоли `py main.py`

Переходим в ранее созданного тг бота и вводим команду `/start`
## Как пользоваться ботом
 Чтобы ответить на сообщение пользователя с ПК (с телефона свайп сообщения) 
 1) ПКМ по сообщению 
 2) `ответить`
 3) Вводим нужное вам сообщение, отправляем

 
 Чтобы просто написать сообщение в чат 

 4) `Написать сообщение`
 5) Вводим сообщение и отправляем






