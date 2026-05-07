from aiogram.filters.callback_data import CallbackData


class MenuCallback(CallbackData, prefix="menu"):
    action: str


class SettingsCallback(CallbackData, prefix="settings"):
    action: str


class DeleteAdminCallback(CallbackData, prefix="delete"):
    id: str
