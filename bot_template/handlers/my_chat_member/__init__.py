from aiogram import Router


def setup_my_chat_member_routers() -> Router:
    from bot_template.handlers.my_chat_member import my_private_status, my_channel_status, my_chat_status

    router = Router()
    router.include_routers(
        my_chat_status.router,
        my_private_status.router,
        my_channel_status.router
    )

    return router
