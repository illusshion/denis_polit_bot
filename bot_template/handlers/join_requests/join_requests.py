import asyncio

from aiogram import Bot, Router, types
from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot_template.db import Channel, User
from bot_template.utils import get_admin, get_captcha, send_captcha_func

router = Router()


@router.chat_join_request()
async def join_request(
        request: types.ChatJoinRequest,
        session: AsyncSession,
        bot: Bot
):
    status = await session.execute(select(Channel.accepting_requests).where(Channel.channel_id == request.chat.id))
    result = status.first()
    if result[0] == "accept":
        await request.approve()
    user_id = request.from_user.id
    check_admin = await get_admin(session=session, user_id=user_id)
    if check_admin is None:
        try:
            captcha = await get_captcha(session)
            await send_captcha_func(bot=bot, chat_id=user_id, captcha=captcha)
        except TelegramRetryAfter as e:
            await asyncio.sleep(e.retry_after)
        except TelegramForbiddenError:
            return
        except:
            pass
    return True
