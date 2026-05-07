from aiogram import Router, types, F, Bot
from aiogram.enums import ContentType
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from sqlalchemy import delete, select, update

from sqlalchemy.ext.asyncio import AsyncSession

from bot_template.db import User, Admin, Captcha, Channel
from bot_template.handlers.callback import MenuCallback, SettingsCallback, DeleteAdminCallback
from bot_template.keyboard.inline_keyboards import settings_buttons, back_button, generate_delete_admin_buttons
from bot_template.keyboard.reply_reyboards import create_turned_off_channels, create_turned_on_channels
from bot_template.states.menu_state import MenuState, SettingsState
from bot_template.utils import get_admin, get_captcha, send_captcha_func

router = Router()


@router.callback_query(
    MenuState.main_menu,
    MenuCallback.filter(
        F.action == "settings"
    )
)
async def settings_menu_func(
        callback: types.CallbackQuery,
        state: FSMContext
):
    await state.clear()
    await callback.message.edit_text(
        "Меню настроек",
        reply_markup=settings_buttons()
    )
    await state.set_state(SettingsState.settings_menu)


@router.callback_query(
    SettingsState.settings_menu,
    SettingsCallback.filter(
        F.action == "add_admin"
    )
)
async def add_admin_button(
        callback: types.CallbackQuery,
        state: FSMContext
):
    await callback.message.edit_text(
        text="Отправь айди пользователя и его позывной. Синтаксиc выглядит так \n<b>id:name</b>",
        parse_mode="html",
        reply_markup=back_button()
    )
    await state.set_state(SettingsState.add_admin_state)


@router.message(
    SettingsState.add_admin_state
)
async def add_admin_func(
        message: types.Message,
        bot: Bot,
        state: FSMContext,
        session: AsyncSession
):
    try:
        user_id = int(message.text.split(":")[0])
        user_name = message.text.split(":")[1]
    except ValueError:
        await message.answer(
             text="Айди не может быть текстом. Попробуй снова.",
             reply_markup=back_button())
        return False
    except IndexError:
        await message.answer(
             text= "Некорректный синтаксис сообщения.\nОтправь по указанному примеру.",
             reply_markup=back_button())
        return False
    check_admin = await get_admin(session=session, user_id=user_id)
    if check_admin is not None:
        await message.reply(
            text="Этот пользователь уже является админом",
            reply_markup=back_button()
        )
        return
    try:
        await bot.send_chat_action(chat_id=user_id, action="typing")
    except TelegramForbiddenError:
        await message.reply(
            text="Бот заблокирован пользователем, либо айди некорректный. Попробуй снова",
            reply_markup=back_button()
        )
        return False
    except TelegramBadRequest:
        await message.reply(
            text="Бот заблокирован пользователем, либо айди некорректный. Попробуй снова",
            reply_markup=back_button()
        )
        return False
    try:
        await session.execute(delete(User).where(User.user_id == user_id))
    except:
        pass
    admin_info = Admin(
        user_id=user_id,
        user_name=user_name
    )
    await session.merge(admin_info)
    await session.commit()
    await message.reply(
        text="Модератор успешно назначен!",
        reply_markup=back_button()
    )
    await state.clear()
    try:
        await bot.set_my_commands([
            types.BotCommand(command="menu", description="Вернуться в меню"),
            types.BotCommand(command="delete", description="Удаление запланированной рассылки по id")
        ],
            scope=types.BotCommandScopeChat(chat_id=user_id))
        await bot.send_message(
            chat_id=user_id,
            text="Вы стали модератором бота!"
        )
    except:
        pass


@router.callback_query(
    SettingsState.settings_menu,
    SettingsCallback.filter(
        F.action == "delete_admin"
    )
)
async def delete_admin_button(
        call: types.CallbackQuery,
        state: FSMContext,
        session: AsyncSession
):
    await call.message.edit_text(
        text="Выбери админа, которого хочешь удалить.",
        reply_markup=await generate_delete_admin_buttons(session)
    )
    await state.set_state(SettingsState.delete_admin_state)


@router.callback_query(
    SettingsState.delete_admin_state,
    DeleteAdminCallback.filter()
)
async def confirm_delete_admin(
        call: types.CallbackQuery,
        state: FSMContext,
        session: AsyncSession,
        bot: Bot,
        callback_data: DeleteAdminCallback
):
    user_id = callback_data.id
    if call.from_user.id == int(user_id):
        await call.message.edit_text(
            text="Не нужно снимать с админки самого себя.",
            reply_markup=back_button()
        )
        return False
    await session.execute(delete(Admin).where(Admin.user_id == int(user_id)))
    await session.commit()
    await call.message.edit_text(
        text="Админ успешно удален!",
        reply_markup=back_button()
    )
    await bot.delete_my_commands(scope=types.BotCommandScopeChat(chat_id=int(user_id)))
    await state.clear()


@router.callback_query(
    SettingsState.settings_menu,
    SettingsCallback.filter(
        F.action == "change_captcha"
    )
)
async def change_captcha(
        call: types.CallbackQuery,
        state: FSMContext
):
    await state.set_state(SettingsState.change_captcha)
    await call.message.edit_text(
        text="Введи текст для капчи. Возможно добавить до 1 видео или фото. Также можно добавить кнопки таким образом:\n<b>{button:текст кнопки}</b>",
        parse_mode="html",
        reply_markup=back_button()
    )


@router.message(
    SettingsState.change_captcha,
    F.content_type == ContentType.TEXT
)
async def change_captcha_text(
        message: types.Message,
        state: FSMContext,
        session: AsyncSession
):
    res = await get_captcha(session)
    captcha = Captcha(
        captcha_text=message.html_text,
        captcha_file=None
    )
    if res is None:
        await session.merge(captcha)
        await session.commit()
        await message.reply(
            text="Капча установлена",
            reply_markup=back_button()
        )
        await state.clear()
    else:
        await session.execute(delete(Captcha))
        await session.merge(captcha)
        await session.commit()
        await message.reply(
            text="Капча установлена",
            reply_markup=back_button()
        )
        await state.clear()


@router.message(
    SettingsState.change_captcha,
    F.content_type == ContentType.VIDEO
)
async def change_captcha_video(
        message: types.Message,
        state: FSMContext,
        session: AsyncSession
):
    res = await get_captcha(session)
    captcha = Captcha(
        captcha_text=message.html_text,
        captcha_file=message.video.file_id
    )
    if res is None:
        await session.merge(captcha)
        await session.commit()
        await message.reply(
            text="Капча установлена",
            reply_markup=back_button()
        )
        await state.clear()
    else:
        await session.execute(delete(Captcha))
        await session.merge(captcha)
        await session.commit()
        await message.reply(
            text="Капча установлена",
            reply_markup=back_button()
        )
        await state.clear()


@router.message(
    SettingsState.change_captcha,
    F.content_type == ContentType.PHOTO
)
async def change_captcha_photo(
        message: types.Message,
        state: FSMContext,
        session: AsyncSession
):
    res = await get_captcha(session)
    captcha = Captcha(
        captcha_text=message.html_text,
        captcha_file=message.photo[0].file_id
    )
    if res is None:
        await session.merge(captcha)
        await session.commit()
        await message.reply(
            text="Капча установлена",
            reply_markup=back_button()
        )
        await state.clear()
    else:
        await session.execute(delete(Captcha))
        await session.merge(captcha)
        await session.commit()
        await message.reply(
            text="Капча установлена",
            reply_markup=back_button()
        )
        await state.clear()


@router.callback_query(
    SettingsState.settings_menu,
    SettingsCallback.filter(
        F.action == "send_captcha"
    )
)
async def send_captcha_button(
        call: types.CallbackQuery,
        bot: Bot,
        session: AsyncSession
):
    captcha = await get_captcha(session)
    await call.message.delete()
    await send_captcha_func(bot=bot, chat_id=call.message.chat.id, captcha=captcha)

@router.callback_query(
    SettingsState.settings_menu,
    SettingsCallback.filter(
        F.action == "turn_off_accepting"
    )
)
async def turn_off_button_func(
    call: types.CallbackQuery,
    state: FSMContext,
    session: AsyncSession
):
    await call.message.delete()
    await call.message.answer(
        text="Выбери нужный канал для отключения автоприема заявок",
        reply_markup=await create_turned_on_channels(session)    
    )
    await state.set_state(SettingsState.reject_requests_state)


@router.callback_query(
    SettingsState.settings_menu,
    SettingsCallback.filter(
        F.action == "turn_on_accepting"
    )
)
async def turn_on_button_func(
    call: types.CallbackQuery,
    state: FSMContext,
    session: AsyncSession
):
    await call.message.delete()
    await call.message.answer(
        text="Выбери нужный канал для включения автоприема заявок",
        reply_markup=await create_turned_off_channels(session)    
    )
    await state.set_state(SettingsState.accept_requests_state)

@router.message(
    SettingsState.reject_requests_state
)
async def reject_requests_from_channels(
    message: types.Message,
    state: FSMContext,
    session: AsyncSession):
    channel = await session.execute(select(Channel).where(Channel.channel_name == message.text))
    result = channel.one_or_none()
    if result is None:
        await message.answer(
            text = "Канал отсутсвует в базе. Попробуй снова",
            reply_markup=await create_turned_on_channels(session)
            )
        return False
    await session.execute(update(Channel).where(Channel.channel_name == message.text).values(accepting_requests="reject"))
    await session.commit()
    await message.answer(
        text="В канале был отключен автоприем заявок.",
        reply_markup=back_button())
    await state.clear()
    
@router.message(
    SettingsState.accept_requests_state
)
async def accept_requests_from_channels(
    message: types.Message,
    state: FSMContext,
    session: AsyncSession):
    channel = await session.execute(select(Channel).where(Channel.channel_name == message.text))
    result = channel.one_or_none()
    if result is None:
        await message.answer(
            text = "Канал отсутсвует в базе. Попробуй снова",
            reply_markup=await create_turned_off_channels(session)
            )
        return False
    await session.execute(update(Channel).where(Channel.channel_name == message.text).values(accepting_requests="accept"))
    await session.commit()
    await message.answer(
        text="В канале был включен автоприем заявок.",
        reply_markup=back_button())
    await state.clear()
