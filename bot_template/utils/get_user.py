from aiogram.types import TelegramObject
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot_template.db import User


async def get_user(event: TelegramObject, session: AsyncSession):
    async with session.begin():
        result = await session.execute(select(User).where(User.user_id == event.from_user.id))
    return result.one_or_none()
