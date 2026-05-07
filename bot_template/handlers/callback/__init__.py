__all__ = ["ConfirmingCallback", "MenuCallback", "DeleteAdminCallback", "SettingsCallback", "CalendarData"]
from bot_template.handlers.callback.menu_callbacks import MenuCallback, DeleteAdminCallback, \
                                                            SettingsCallback
from bot_template.handlers.callback.confirming_sending import ConfirmingCallback, CalendarData

from aiogram import Router


def setup_callback_routers() -> Router:
    from bot_template.handlers.callback import main_menu, settings

    router = Router()
    router.include_routers(
        main_menu.router,
        settings.router
    )

    return router
