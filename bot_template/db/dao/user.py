from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot_template.db import Admin, User


class _UserRepo:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_all_ids(self) -> list[int]:
        return list(await self.session.scalars(select(User.user_id).limit(None)))

    async def get_admin_ids(self) -> list[int]:
        return list(await self.session.scalars(select(Admin.user_id).limit(None)))

