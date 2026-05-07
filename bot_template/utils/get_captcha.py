from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot_template.db import Captcha


async def get_captcha(session: AsyncSession):
    captcha = await session.execute(select(Captcha))
    return captcha.scalar_one_or_none()
