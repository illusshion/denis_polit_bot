import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand, BotCommandScopeChat
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.redis import RedisJobStore
from apscheduler_di import ContextSchedulerDecorator
from aiogram.fsm.storage.redis import RedisStorage
from environs import Env
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from bot_template.db.dao.repo import DbRepo

from bot_template.db import Admin
from bot_template.handlers import (setup_callback_routers,
                                   setup_commands_routers,
                                   setup_join_requests_routers,
                                   setup_my_chat_member_routers)
from bot_template.middlewares import (AccessCallbackMiddleware,\
 AccessMiddleware, AlbumMiddleware,\
                   DbSessionMiddleware)

logging.basicConfig(level=logging.DEBUG)

env = Env()
env.read_env()

async def main():
    async_engine = create_async_engine(
        url=env.str("POSTGRES_URL"),
        echo=False,
        pool_pre_ping=True
    )
    session_maker = async_sessionmaker(async_engine, expire_on_commit=False)

    bot = Bot(token=env.str("BOT_TOKEN"), parse_mode="html")

    async with session_maker() as session:
        try:
            await asyncio.gather(*[
                bot.set_my_commands(
                    [
                        BotCommand(command="menu", description="Вернуться в меню"),
                        BotCommand(command="delete", description="Удаление запланированной рассылки по id")
                    ],
                    scope=BotCommandScopeChat(chat_id=admin_id)
                )
                for admin_id in list(await session.scalars(select(Admin.user_id).limit(None)))
            ])
        except:
            pass
    
    dp = Dispatcher(storage=RedisStorage.from_url("redis://redis:6379/0"))
    jobstores = {
        'default': RedisJobStore(jobs_key='dispatched_trips_jobs',
                                 run_times_key='dispatched_trips_running',
                                 host='redis',
                                 db=2,
                                 port=6379)
    }

    scheduler = ContextSchedulerDecorator(AsyncIOScheduler(timezone="Europe/Kiev", jobstores=jobstores))
    scheduler.ctx.add_instance(bot, declared_class=Bot)
    scheduler.ctx.add_instance(session_maker, declared_class=async_sessionmaker)

    scheduler.start()

    dp.update.outer_middleware(DbSessionMiddleware(session_pool=session_maker))
    dp.message.outer_middleware(AccessMiddleware()) 
    dp.callback_query.outer_middleware(AccessCallbackMiddleware())
    dp.message.middleware(AlbumMiddleware())

    dp.include_routers(
        setup_commands_routers(),
        setup_my_chat_member_routers(),
        setup_join_requests_routers(),
        setup_callback_routers()
    )
    try:
        await dp.start_polling(bot, scheduler=scheduler)
    finally:
        await dp.storage.close()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
