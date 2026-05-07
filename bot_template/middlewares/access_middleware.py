from typing import Any, Awaitable, Callable, Dict

from aiogram.dispatcher.middlewares.base import BaseMiddleware
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select

from bot_template.utils import get_admin
from bot_template.db import User
from bot_template.keyboard.reply_reyboards import news_markup


class AccessMiddleware(BaseMiddleware):

    async def __call__(
            self,
            handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
            event: Message,
            data: Dict[str, Any],
    ) -> Any:
        session = data["session"]
        result = await get_admin(event.from_user.id, session)
        if result is None:
            actually_text = ["Новости дня", "Последняя новость"]
            if event.text in actually_text:
                return await handler(event, data)
            exists = await session.execute(select(User).where(User.user_id == event.from_user.id))
            if not exists.one_or_none():
                user_info = User(
                    user_id=event.from_user.id
            )
                await session.merge(user_info)
                await session.commit()
            await event.answer("<b>Здравствуйте! Выберите интересный вам пункт.</b>", parse_mode="html", reply_markup=news_markup())
            return
        return await handler(event, data)


class AccessCallbackMiddleware(BaseMiddleware):

    async def __call__(
            self,
            handler: Callable[[CallbackQuery, Dict[str, Any]], Awaitable[Any]],
            event: CallbackQuery,
            data: Dict[str, Any],
    ) -> Any:
        session = data["session"]
        result = await get_admin(event.from_user.id, session)
        if result is None:
            return
        return await handler(event, data)
