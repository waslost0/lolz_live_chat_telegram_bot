import json
import logging
import sys
import threading

import aiogram.utils.markdown as fmt
from aiogram import Bot, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import IsReplyFilter
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils import executor
from loguru import logger

from keyboards import main_keyboard, notification_keyboard, cancel_keyboard
from lolz import LolzWorker
from utils import load_data_from_file


def check_data_json(data: dict):
    for item in data.keys():
        if 'telegram' in item:
            telegram_id = data.get('telegram').get('telegram_id')
            if telegram_id == '':
                logger.error('Не заполнен telegram_id')
                return False
            bot_token = data.get('telegram').get('bot_token')
            if bot_token == '':
                logger.error('Не заполнен bot_token')
                return False
    return True


config = {
    "handlers": [
        {"sink": sys.stderr, "level": logging.DEBUG, "backtrace": True},
        {"sink": "logs.log", "level": "DEBUG", "rotation": "5 MB", "encoding": "utf8", "backtrace": True,
         "retention": "1 day"},
    ],
}

logger.configure(**config)

DATA_JSON = load_data_from_file()
if not check_data_json(DATA_JSON):
    sys.exit()

ADMINS_ID = DATA_JSON["telegram"]["telegram_id"]
bot = Bot(token=DATA_JSON["telegram"]["bot_token"])
dp = Dispatcher(bot, storage=MemoryStorage())
lolz = LolzWorker(DATA_JSON)


class States(StatesGroup):
    wait_for_message = State()


def validate_json(json_data):
    try:
        json.loads(json_data)
    except ValueError as err:
        return False
    return True


@dp.message_handler(text="💴 Баланс")
@dp.message_handler(commands="get_balance")
async def get_balance(message: types.Message):
    if str(message.chat.id) in ADMINS_ID:
        balance = await lolz.get_balance()
        await message.answer(f"💶 Баланс: {balance}")


@dp.message_handler(text="Уведомления лолза")
async def get_balance(message: types.Message):
    if str(message.chat.id) in ADMINS_ID:
        notif = await lolz.get_new_notifications()
        message_send = ''
        if notif:
            for item in notif.values():
                text = item.get('text').strip()
                username = item.get('username')
                user_link = item.get('user_link')
                post_link_text = item.get('post_link_text')
                post_link = item.get('post_link')
                if 'root' in text:
                    text = text.replace(username, f'<b><a href="{user_link}">{username}</a></b>')
                    text = text.replace('\nhttps', '\n  https')
                    message_send += f'• {text}\n  <b>{item.get("time").strip()}</b>\n\n'
                else:
                    text = text.replace(username, f'<b><a href="{user_link}">{username}</a></b>')
                    text = text.replace(post_link_text, f'<b><a href="{post_link}">{post_link_text}</a></b>')
                    message_send += f'• {text}\n  <b>{item.get("time").strip()}</b>\n\n'
        else:
            await message.answer('Нет новых уведомлений')
            return
        await message.answer(message_send, parse_mode=types.ParseMode.HTML)


@dp.message_handler(text="Назад")
async def info_mode(message: types.Message):
    if str(message.chat.id) in ADMINS_ID:
        text = 'Главное меню'
        await message.answer(text, reply_markup=main_keyboard)


@dp.message_handler(text="Cancel", state="*")
async def cmd_cancel(message: types.Message, state: FSMContext):
    if str(message.chat.id) in ADMINS_ID:
        await state.finish()
        await message.answer("Действие отменено", reply_markup=main_keyboard)


def start_participate():
    my_thread = threading.Thread(target=lolz.participate_in_contests)
    my_thread.start()


async def set_default_commands(dp):
    await dp.bot.set_my_commands([
        types.BotCommand("start", "Start bot. Show keyboard"),
        types.BotCommand("get_balance", "Get balance")
    ])


@dp.message_handler(commands="start")
async def cmd_start(message: types.Message):
    if str(message.chat.id) in ADMINS_ID:
        await message.answer("q", reply_markup=main_keyboard)


@dp.callback_query_handler(text="turn_off_info_mode")
async def turn_off_info_mod(call: types.CallbackQuery):
    if lolz.user_data["telegram"]["info_mod"]:
        lolz.user_data["telegram"]["info_mod"] = False
        lolz.is_info_mod = False
        save_data_to_file(lolz.user_data)
        await call.answer(text="Info Mode is OFF", show_alert=True)
    else:
        await call.answer(text="Info Mode is already OFF", show_alert=True)


@dp.message_handler(commands='info_mod')
@dp.message_handler(text="Info mode")
async def info_mode(message: types.Message):
    if str(message.chat.id) in ADMINS_ID:
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton(text="Включить", callback_data="turn_on_info_mode"))
        keyboard.add(types.InlineKeyboardButton(text="Выключить", callback_data="turn_off_info_mode"))
        info = "ON" if lolz.is_info_mod else "OFF"
        await message.answer(
            fmt.text(
                fmt.text("Info mode is ", fmt.hbold(info))
            ),
            parse_mode="HTML",
            reply_markup=keyboard)


@dp.message_handler(text=['Написать сообщение'])
async def info_mode(message: types.Message):
    if str(message.chat.id) in ADMINS_ID:
        await message.answer('Отправь мне сообщение', reply_markup=cancel_keyboard)
        await States.wait_for_message.set()


@dp.message_handler(state=[States.wait_for_message],
                    content_types=types.ContentTypes.TEXT)
async def sleep_time_state(message: types.Message, state: FSMContext):
    if str(message.chat.id) in ADMINS_ID:
        if lolz.send_message(message.text):
            await message.answer('Сообщение отправлено', reply_markup=main_keyboard)
        else:
            await message.answer('Не смог отправить сообщение', reply_markup=main_keyboard)
        await state.finish()


@dp.message_handler(IsReplyFilter(True))
async def info_mode(message: types.Message):
    if str(message.chat.id) in ADMINS_ID:
        if message.reply_to_message:
            temp_message = ''
            user_to_reply = message.reply_to_message.text.split(':')[0].strip()
            temp_message = f'@{user_to_reply}, {message.text}'
            logger.debug(temp_message)
            if lolz.send_message(temp_message):
                await message.answer('Сообщение отправлено')
            else:
                await message.answer('Не смог отправить сообщение')


@dp.message_handler(text="Уведомления тг")
async def info_mode(message: types.Message):
    if str(message.chat.id) in ADMINS_ID:
        text = 'Настройка уведомлений'
        await message.answer(text, reply_markup=notification_keyboard)


@dp.message_handler(text="Error mode")
@dp.message_handler(commands='error_mod')
async def error_mode(message: types.Message):
    if str(message.chat.id) in ADMINS_ID:
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton(text="Включить", callback_data="turn_on_error_mode"))
        keyboard.add(types.InlineKeyboardButton(text="Выключить", callback_data="turn_off_error_mode"))
        info = "ON" if lolz.is_error_mode else "OFF"
        await message.answer(
            fmt.text(
                fmt.text("Error mode is ", fmt.hbold(info))
            ),
            parse_mode="HTML",
            reply_markup=keyboard)


@dp.callback_query_handler(text="turn_off_info_mode")
async def turn_off_info_mod(call: types.CallbackQuery):
    if lolz.user_data["telegram"]["info_mod"]:
        lolz.user_data["telegram"]["info_mod"] = False
        lolz.is_info_mod = False
        save_data_to_file(lolz.user_data)
        await call.answer(text="Info Mode is OFF", show_alert=True)
    else:
        await call.answer(text="Info Mode is already OFF", show_alert=True)


@dp.callback_query_handler(text="turn_off_error_mode")
async def turn_off_error_mod(call: types.CallbackQuery):
    if lolz.user_data["telegram"]["error_mod"]:
        lolz.user_data["telegram"]["error_mod"] = False
        lolz.is_error_mode = False
        save_data_to_file(lolz.user_data)
        await call.answer(text="Error Mode is OFF", show_alert=True)
    else:
        await call.answer(text="Error Mode is already OFF", show_alert=True)


@dp.callback_query_handler(text="turn_on_info_mode")
async def turn_on_info_mod(call: types.CallbackQuery):
    if not lolz.user_data["telegram"]["info_mod"]:
        lolz.user_data["telegram"]["info_mod"] = True
        lolz.is_info_mod = True
        save_data_to_file(lolz.user_data)
        await call.answer(text="Info mode is ON", show_alert=True)
    else:
        await call.answer(text="Info mode is already ON", show_alert=True)


@dp.callback_query_handler(text="turn_on_error_mode")
async def turn_on_info_mod(call: types.CallbackQuery):
    if not lolz.user_data["telegram"]["error_mod"]:
        lolz.user_data["telegram"]["error_mod"] = True
        lolz.is_error_mode = True
        save_data_to_file(lolz.user_data)
        await call.answer(text="Error mode is ON", show_alert=True)
    else:
        await call.answer(text="Error mode is already ON", show_alert=True)


def save_data_to_file(data):
    try:
        temp_data = {}
        with open("data.json", "r+") as json_file:
            temp_data = json.load(json_file)

        for key in data:
            temp_data[key] = data[key]

        with open("data.json", "w+") as json_file:
            json.dump(data, json_file, indent=4)

    except KeyError as error:
        print("Cannot find: %s", error.args[0])


async def on_startup(dp):
    await set_default_commands(dp)
    if lolz.is_login():
        logger.info("Login successful")
        start_participate()
    else:
        logger.info("Login fail")


if __name__ == "__main__":
    executor.start_polling(dp, on_startup=on_startup, skip_updates=True)
