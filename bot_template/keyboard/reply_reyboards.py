from aiogram.types import KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot_template.db import Channel


async def create_turned_on_channels(session: AsyncSession):
    builder = ReplyKeyboardBuilder()
    channels = await session.execute(select(Channel.channel_name).where(Channel.accepting_requests == "accept"))
    for channel_name in channels:
        builder.add(KeyboardButton(
            text=channel_name[0]
        )
    )
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)


async def create_turned_off_channels(session: AsyncSession):
    builder = ReplyKeyboardBuilder()
    channels = await session.execute(select(Channel.channel_name).where(Channel.accepting_requests == "reject"))
    for channel_name in channels:
        builder.add(KeyboardButton(
            text=channel_name[0]
        )
    )
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)

def news_markup():
    builder = ReplyKeyboardBuilder()

    builder.button(text="Новости дня")
    builder.button(text="Последняя новость")

    builder.adjust(1)

    return builder.as_markup(resize_keyboard=True)