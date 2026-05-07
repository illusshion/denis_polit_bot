from aiogram import Router


def setup_commands_routers() -> Router:
    from bot_template.handlers.commands import sending, start, news

    router = Router()
    router.include_routers(
        sending.router,
        start.router,
        news.router
    )

    return router
