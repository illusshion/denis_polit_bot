from aiogram import Bot, F, Router, types
from aiogram.enums import ChatType
from aiogram.filters.chat_member_updated import MEMBER, ChatMemberUpdatedFilter

router = Router()
router.my_chat_member.filter(F.chat.type.in_([ChatType.GROUP, ChatType.SUPERGROUP]))


@router.my_chat_member(
    ChatMemberUpdatedFilter(member_status_changed=MEMBER)
)
async def bot_added_to_group(
        event: types.ChatMemberUpdated,
        bot: Bot
):
    await bot.leave_chat(
        chat_id=event.chat.id
    )