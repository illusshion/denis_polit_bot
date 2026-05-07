import re

from aiogram import Bot, types
from aiogram.exceptions import TelegramBadRequest
from aiogram.utils.keyboard import ReplyKeyboardBuilder


async def send_captcha_func(bot: Bot, captcha, chat_id):
    PATTERN = re.compile(r"({button:)(.*?)(})")
    builder = ReplyKeyboardBuilder()
    for i in re.findall(PATTERN, string=captcha.captcha_text):
        builder.add(types.KeyboardButton(text=i[1]))
    text = re.sub(PATTERN, repl="", string=captcha.captcha_text)
    builder.adjust(1)
    keyboard = builder.as_markup(resize_keyboard=True, one_time_keyboard=True)
    if captcha.captcha_file is None:
        return await bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode="html",
            reply_markup=keyboard
        )
    else:
        try:
            return await bot.send_video(
                chat_id=chat_id,
                video=captcha.captcha_file,
                caption=text,
                parse_mode="html",
                reply_markup=keyboard
            )
        except TelegramBadRequest:
            return await bot.send_photo(
                chat_id=chat_id,
                photo=captcha.captcha_file,
                caption=text,
                parse_mode="html",
                reply_markup=keyboard
            )
