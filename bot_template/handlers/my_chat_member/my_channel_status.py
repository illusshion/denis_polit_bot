from aiogram import F, Router, types
from aiogram.enums import ChatType
from aiogram.filters.chat_member_updated import (ADMINISTRATOR, IS_NOT_MEMBER,
                                                 ChatMemberUpdatedFilter)
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from bot_template.db import Channel
from bot_template.db.dao.repo import DbRepo

router = Router()
router.my_chat_member.filter(F.chat.type == ChatType.CHANNEL)


@router.my_chat_member(
    ChatMemberUpdatedFilter(
        member_status_changed=ADMINISTRATOR >> IS_NOT_MEMBER
    )
)
async def bot_kicked_from_channel(
        event: types.ChatMemberUpdated,
        session: AsyncSession
):  
    async with session.begin():
        await session.execute(delete(Channel).where(Channel.channel_id == event.chat.id))


@router.my_chat_member(
    ChatMemberUpdatedFilter(
        member_status_changed=ADMINISTRATOR
    )
)
async def bot_added_to_channel(
        event: types.ChatMemberUpdated,
        session: AsyncSession,
        db: DbRepo
):
    admins = await db.user.get_admin_ids()
    if event.from_user.id not in admins:
        return
    async with session.begin():
        channel_info = Channel(
                channel_id=event.chat.id,
                channel_name=event.chat.full_name,
                accepting_requests="accept"
            )
        await session.merge(channel_info)
