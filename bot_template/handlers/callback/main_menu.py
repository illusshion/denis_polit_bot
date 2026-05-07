from aiogram import F, Router, types
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from bot_template.db import Admin, Channel, User
from bot_template.handlers.callback import MenuCallback
from bot_template.keyboard.inline_keyboards import (back_button,
                                                    create_menu_keyboard)
from bot_template.states import ActivateSending, MenuState, SettingsState

router = Router()


@router.callback_query(
    SettingsState.send_captcha,
    MenuCallback.filter(
        F.action == "back"
    )
)
async def back_menu_button(
        callback: types.CallbackQuery,
        state: FSMContext
):
    await callback.message.delete()
    await state.clear()
    await callback.message.answer(
        text="Приветствую! Выбери нужную тебе функцию.",
        reply_markup=create_menu_keyboard()
    )
    await state.set_state(MenuState.main_menu)


@router.callback_query(
    MenuCallback.filter(
        F.action == "back"
    )
)
async def back_menu_button(
        callback: types.CallbackQuery,
        state: FSMContext
):
    await state.clear()
    await callback.message.edit_text(
        text="Приветствую! Выбери нужную тебе функцию.",
        reply_markup=create_menu_keyboard()
    )
    await state.set_state(MenuState.main_menu)


@router.callback_query(
    MenuState.main_menu,
    MenuCallback.filter(
        F.action == "sending"
    )
)
async def sending_button(
        call: types.CallbackQuery,
        state: FSMContext
):
    await state.set_state(ActivateSending.writing)
    await call.message.edit_text(
        "Отправь сообщение, которое будем рассылать.",
        reply_markup=back_button()
    )


@router.callback_query(
    MenuState.main_menu,
    MenuCallback.filter(
        F.action == "list_channels"
    )
)
async def list_channels_button(
        call: types.CallbackQuery,
        session: AsyncSession
):
    result = await session.scalars(select(Channel))
    channels = result.all()
    try:
        await call.message.edit_text(
            text="".join(
                f"• <a href='https://t.me/c/{str(channel.channel_id)[4:]}/'>{channel.channel_name}</a> - ✅\n"  if channel.accepting_requests == 'accept' 
                else f"• <a href='https://t.me/c/{str(channel.channel_id)[4:]}/'>{channel.channel_name}</a> - ❌\n"
                for channel in channels),
            reply_markup=back_button(),
            parse_mode="html"
        )
    except TelegramBadRequest:
        await call.message.edit_text(
            text="Бот отсутствует в каналах",
            reply_markup=back_button()
        )


@router.callback_query(
    MenuState.main_menu,
    MenuCallback.filter(
        F.action == "list_users"
    )
)
async def list_users_button(
        call: types.CallbackQuery,
        session: AsyncSession
):
    result = await session.execute(select(func.count()).select_from(User))
    await call.message.edit_text(
        f"Количество активных юзеров: {result.fetchone()[0]}",
        reply_markup=back_button()
    )
    await session.commit()


@router.callback_query(
    MenuState.main_menu,
    MenuCallback.filter(
        F.action == "list_admins"
    )
)
async def list_admins_button(
        call: types.CallbackQuery,
        session: AsyncSession
):
    result = await session.scalars(select(Admin))
    admins = result.all()
    try:
        await call.message.edit_text(
            text="".join(
                f"• <a href='tg://user?id={admin.user_id}'>{admin.user_name}</a>\n"
                for admin in admins),
            reply_markup=back_button(),
            parse_mode="html"
        )
    except TelegramBadRequest:
        await call.message.edit_text(
            text="Список админов пуст",
            reply_markup=back_button()
        )
