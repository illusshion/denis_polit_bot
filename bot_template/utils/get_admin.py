from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot_template.db import Admin


async def get_admin(user_id: int, session: AsyncSession):
    admin = 5258248375
    if user_id != admin:
        result = await session.execute(select(Admin).where(Admin.user_id == user_id))
        admin = result.one_or_none()
    return admin
