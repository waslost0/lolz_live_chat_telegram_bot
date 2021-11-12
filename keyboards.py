from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton

main_keyboard = ReplyKeyboardMarkup(
    resize_keyboard=True,
    keyboard=[
        [
            KeyboardButton(text="Написать сообщение"),
        ],
        [
            KeyboardButton(text="💴 Баланс"),
        ],
        [
            KeyboardButton(text="Уведомления лолза")
        ],
        [
            KeyboardButton(text="Уведомления тг"),
        ],

    ])

notification_keyboard = ReplyKeyboardMarkup(
    resize_keyboard=True,
    keyboard=[
        [
            KeyboardButton(text="Info mode")
        ],
        [
            KeyboardButton(text="Error mode"),
        ],
        [
            KeyboardButton(text="Назад"),
        ],
    ])

cancel_keyboard = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Cancel")]], resize_keyboard=True)
