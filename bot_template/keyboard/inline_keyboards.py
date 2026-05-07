from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot_template.db import Admin
from bot_template.handlers.callback.confirming_sending import \
    ConfirmingCallback
from bot_template.handlers.callback.menu_callbacks import (DeleteAdminCallback,
                                                           MenuCallback,
                                                           SettingsCallback)


def create_menu_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(
        text="Рассылка 📢",
        callback_data=MenuCallback(
            action="sending"
        ).pack()
    )
    builder.button(
        text="Список каналов 📋",
        callback_data=MenuCallback(
            action="list_channels"
        ).pack()
    )
    builder.button(
        text="Список новостей 🗞",
        callback_data=MenuCallback(
            action="list_news"
        ).pack()
    )
    builder.button(
        text="Список админов 🛠",
        callback_data=MenuCallback(
            action="list_admins"
        ).pack()
    )
    builder.button(
        text="Количество активных юзеров 🤖",
        callback_data=MenuCallback(
            action="list_users"
        ).pack()
    )
    builder.button(
        text="Настройки ⚙️",
        callback_data=MenuCallback(
            action="settings"
        ).pack()
    )

    builder.adjust(1)
    return builder.as_markup()


def settings_buttons():
    builder = InlineKeyboardBuilder()

    builder.button(
        text="Добавление админа",
        callback_data=SettingsCallback(
            action="add_admin"
        ).pack()
    )
    builder.button(
        text="Удаление админа",
        callback_data=SettingsCallback(
            action="delete_admin"
        ).pack()
    )
    builder.button(
        text="Смена капчи",
        callback_data=SettingsCallback(
            action="change_captcha"
        ).pack()
    )
    builder.button(
        text="Просмотр капчи",
        callback_data=SettingsCallback(
            action="send_captcha"
        ).pack()
    )
    builder.button(
        text="Включить автоприем",
        callback_data=SettingsCallback(
        action="turn_on_accepting"
        ).pack()
    )
    builder.button(
        text="Отключить автоприем",
        callback_data=SettingsCallback(
        action="turn_off_accepting"
        ).pack()
    )
    
    builder.button(
        text="Добавить новости",
        callback_data=SettingsCallback(
        action="add_news"
        ).pack()
    )

    builder.button(
        text="Удалить новости",
        callback_data=SettingsCallback(
        action="delete_news"
        ).pack()
    )

    builder.button(
        text="Назад",
        callback_data=MenuCallback(
            action="back"
        ).pack()
    )

    builder.adjust(2)

    return builder.as_markup()

def confirm_mailing():
    builder = InlineKeyboardBuilder()

    builder.button(
        text="Добавить кнопки",
        callback_data=ConfirmingCallback(
            action="add_buttons"
        ).pack()
    )
    builder.button(
        text="Подтвердить",
        callback_data=ConfirmingCallback(
            action="sure"
        ).pack()
    )
    builder.button(
        text="Запланировать",
        callback_data=ConfirmingCallback(
            action="schedule"
        ).pack()
    )
    builder.button(
        text="Отклонить",
        callback_data=MenuCallback(
            action="back"
        ).pack()
    )
    builder.adjust(1, 2, 1)
    return builder.as_markup()


def confirm_mailing_media_group():
    builder = InlineKeyboardBuilder()

    builder.button(
        text="Подтвердить",
        callback_data=ConfirmingCallback(
            action="sure"
        ).pack()
    )
    builder.button(
        text="Запланировать",
        callback_data=ConfirmingCallback(
            action="schedule"
        ).pack()
    )
    builder.button(
        text="Отклонить",
        callback_data=MenuCallback(
            action="back"
        ).pack()
    )
    builder.adjust(2, 1)
    return builder.as_markup()


def stop_mailing():
    builder = InlineKeyboardBuilder()

    builder.button(
        text="Остановить",
        callback_data=ConfirmingCallback(
            action="stop"
        ).pack()
    )

    return builder.as_markup()


async def generate_delete_admin_buttons(session: AsyncSession):
    builder = InlineKeyboardBuilder()
    admins_sql = await session.scalars(select(Admin))
    admins = admins_sql.all()
    for i in admins:
        builder.button(
            text=f"{i.user_name}",
            callback_data=DeleteAdminCallback(
                id=f"{i.user_id}"
            ).pack()
        )
    builder.button(
        text="<- Назад",
        callback_data=MenuCallback(
            action="back"
        ).pack()
    )
    builder.adjust(1)
    return builder.as_markup()


def back_button():
    builder = InlineKeyboardBuilder()

    builder.button(
        text="Назад",
        callback_data=MenuCallback(
            action="back"
        ).pack()
    )

    return builder.as_markup()
