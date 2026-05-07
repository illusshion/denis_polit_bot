from aiogram import Router


def setup_join_requests_routers() -> Router:
    from bot_template.handlers.join_requests import join_requests

    router = Router()
    router.include_router(
        join_requests.router
    )

    return router