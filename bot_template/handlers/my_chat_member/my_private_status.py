from aiogram import F, Router
from aiogram.enums import ChatType
from aiogram.filters.chat_member_updated import (KICKED, MEMBER,
                                                 ChatMemberUpdatedFilter)
from aiogram.types import ChatMemberUpdated
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from bot_template.db import User
from bot_template.utils import get_admin

router = Router()
router.my_chat_member.filter(F.chat.type == ChatType.PRIVATE)


@router.my_chat_member(
    ChatMemberUpdatedFilter(member_status_changed=KICKED)
)
async def user_blocked_bot(
        event: ChatMemberUpdated,
        session: AsyncSession
):
    async with session.begin():
        await session.execute(delete(User).where(User.user_id == event.from_user.id))
