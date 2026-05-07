import asyncio
import datetime
from typing import List, Union
import ujson as json
import re
from zoneinfo import ZoneInfo

from apscheduler_di import ContextSchedulerDecorator
from aiogram import Bot, F, Router, types
from aiogram.filters import Command, CommandObject
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import async_sessionmaker

from bot_template.db.dao.repo import DbRepo
from bot_template.utils.calendar import Calendar
from bot_template.handlers.callback import ConfirmingCallback, CalendarData
from bot_template.keyboard.inline_keyboards import (back_button,
                                                    confirm_mailing, confirm_mailing_media_group,
                                                    stop_mailing)
from bot_template.states import ActivateSending
from bot_template.workers.mailing import Mailing

InputMedia = Union[
    types.InputMediaPhoto, types.InputMediaVideo,
    types.InputMediaAudio, types.InputMediaDocument
]

async def schedule_mail_group(data: dict, from_chat_id, bot: Bot, session_maker: async_sessionmaker):
    async with session_maker() as session:
        db = DbRepo(session)
        album_pack = data.get("album_pack")
        m = await bot.send_message(
            chat_id=from_chat_id,
            text="Запланированная рассылка начнется через несколько секунд.", 
            reply_markup=stop_mailing()
        )
        mailing = Mailing()
        admins = await db.user.get_admin_ids()
        users = await db.user.get_all_ids()
        all_us = admins + users

    asyncio.create_task(mailing.sending_media_group(
        users=all_us,
        bot=bot,
        media_group_pack=album_pack,
        from_chat_id=from_chat_id,
        notif_msg_id=m.message_id
    ))
    await m.edit_text("<i>Запланированная рассылка успешно начата. \nРассылку получат: {} пользователей</i>".format(len(users)), parse_mode="html", reply_markup=stop_mailing())

async def schedule_mail(data: dict, from_chat_id, bot: Bot, session_maker: async_sessionmaker):
    async with session_maker() as session:
        db = DbRepo(session)
        message_id = data.get("msg_id")
        reply_markup = data.get("reply_markup")
        m = await bot.send_message(
            chat_id=from_chat_id,
            text="Запланированная рассылка начнется через несколько секунд.",
            reply_markup=stop_mailing()
        )
        mailing = Mailing()
        admins = await db.user.get_admin_ids()
        users = await db.user.get_all_ids()
        all_us = admins + users

    asyncio.create_task(mailing.copy_sending(
        users=all_us,
        bot=bot,
        message_id=message_id,
        from_chat_id=from_chat_id,
        notif_msg_id=m.message_id,
        reply_markup=reply_markup
    ))
    await m.edit_text("<i>Запланированная рассылка успешно начата. \nРассылку получат: {} пользователей</i>".format(len(users)), parse_mode="html", reply_markup=stop_mailing())

router = Router()

@router.message(Command("delete"))
async def delete_schedule(message: types.Message, command: CommandObject, scheduler: ContextSchedulerDecorator):
    args = command.args
    if not args:
        await message.answer("Вы не указали id!")
        return
    scheduler.remove_job(args)
    await message.answer("Запланированная рассылка по этому id была успешно отменена!")

@router.message(
    F.media_group_id,
    ActivateSending.writing
)
async def sending_media_group_func(
        message: types.Message,
        state: FSMContext,
        album: List[types.Message]
):
    group_elements = []
    for element in album:
        caption_kwargs = {"caption": element.html_text, "caption_entities": element.caption_entities, "parse_mode": "html"}
        if element.photo:
            input_media = types.InputMediaPhoto(media=element.photo[-1].file_id, **caption_kwargs)
        elif element.video:
            input_media = types.InputMediaVideo(media=element.video.file_id, **caption_kwargs)
        elif element.document:
            input_media = types.InputMediaDocument(media=element.document.file_id, **caption_kwargs)
        elif element.audio:
            input_media = types.InputMediaAudio(media=element.audio.file_id, **caption_kwargs)
        else:
            return message.answer("This media type isn't supported!")
        group_elements.append(input_media)
    await message.answer_media_group(group_elements)
    await message.answer(
        text="Подтвердите начало рассылки.",
        reply_markup=confirm_mailing_media_group()
    )

    album = [model.model_dump() for model in group_elements]
    pack_album = json.dumps(album)

    await state.set_state(ActivateSending.choosing_media_group)
    await state.set_data({"album_pack": pack_album})


@router.message(
    ActivateSending.writing
)
async def sending_func(
        message: types.Message,
        bot: Bot,
        state: FSMContext
):
    m = await bot.copy_message(
        chat_id=message.chat.id,
        from_chat_id=message.chat.id,
        message_id=message.message_id,
        reply_markup=message.reply_markup
    )
    await message.answer(
        text="Подтвердите начало рассылки.",
        reply_markup=confirm_mailing()
    )
    await state.set_state(ActivateSending.choosing)
    if message.reply_markup:
        await state.set_data({"msg_id": m.message_id, "reply_markup": json.dumps(message.reply_markup.model_dump())})
    else:
        await state.set_data({"msg_id": m.message_id, "reply_markup": "None"})

@router.callback_query(ConfirmingCallback.filter(
                        F.action == "add_buttons"
                    ),
                    ActivateSending.choosing

)
async def add_buttons_button(call: types.CallbackQuery, state: FSMContext):
    await call.message.edit_text(text="Здесь вы можете добавить url кнопки.\nСинтаксис как в телепосте:\n<b>Кнопка 1 - example.com/</b>", parse_mode="html")
    await state.set_state(ActivateSending.add_button)


@router.callback_query(F.data == "default", ActivateSending.schedule)
async def back_default(call: types.CallbackQuery, state: FSMContext):
    await call.message.edit_text("Подтвердите начало рассылки", reply_markup=confirm_mailing())
    await state.set_state(ActivateSending.choosing)


@router.callback_query(F.data == "group", ActivateSending.schedule_group)
async def back_group(call: types.CallbackQuery, state: FSMContext):
    await call.message.edit_text("Подтвердите начало рассылки", reply_markup=confirm_mailing_media_group())
    await state.set_state(ActivateSending.choosing_media_group)


@router.message(ActivateSending.add_button)
async def extract_data(message: types.Message, state: FSMContext, bot: Bot):
    line_pattern = r'(.+?)[ -]+((?:https?://)?[A-Za-z0-9.-]+\.[A-Za-z]{2,6}\S*)\s*(?:\||$)'
    builder = InlineKeyboardBuilder()
    sizes = []
    data = await state.get_data()
    msg_id = data.get("msg_id")
    button_data_lines = message.text.strip().split('\n')
    for line in button_data_lines:
        parted = re.findall(line_pattern, line)
        if parted:
            sizes.append(len(parted))
            for i in parted:
                builder.button(text=i[0].strip(), url=i[1].strip())
    builder.adjust(*sizes)
    m = await bot.copy_message(chat_id=message.from_user.id, from_chat_id=message.from_user.id, message_id=msg_id, reply_markup=builder.as_markup())
    await message.answer("Подтвердите начало рассылки", reply_markup=confirm_mailing())
    await state.set_state(ActivateSending.choosing)
    await state.set_data({"msg_id": m.message_id, "reply_markup": json.dumps((builder.as_markup()).model_dump())})

    
@router.callback_query(
    ActivateSending.choosing_media_group,
    ConfirmingCallback.filter(
        F.action == "sure"
    )
)
async def sending_media_group_func(
        call: types.CallbackQuery,
        state: FSMContext,
        db: DbRepo,
        bot: Bot
):
    data = await state.get_data()
    album_pack = data.get("album_pack")
    await call.message.edit_text(
        text="Рассылка начнется через несколько секунд.", 
        reply_markup=stop_mailing()
    )
    mailing = Mailing()
    admins = await db.user.get_admin_ids()
    users = await db.user.get_all_ids()
    all_us = admins + users

    asyncio.create_task(mailing.sending_media_group(
        users=all_us,
        bot=bot,
        media_group_pack=album_pack,
        from_chat_id=call.from_user.id,
        notif_msg_id=call.message.message_id
    ))
    await call.message.edit_text("<i>Рассылка успешно начата. \nРассылку получат: {} пользователей</i>".format(len(users)), parse_mode="html", reply_markup=stop_mailing())
    await state.clear()


@router.callback_query(
        ActivateSending.choosing,
        ConfirmingCallback.filter(
            F.action == "schedule"
        )
)
async def schedule_mailing(
        call: types.CallbackQuery, state: FSMContext):
        calendar_obj = Calendar()
        date = datetime.datetime.now(tz=ZoneInfo("Europe/Kiev"))
        currect_year = date.year
        currect_month = date.month
        currect_day = date.day
        await call.message.edit_text(text="Выберите нужную дату и напишите желаемое время", reply_markup=calendar_obj.generate_calendar(currect_year, currect_month, currect_year, currect_month, currect_day, "default"))
        await state.set_state(ActivateSending.schedule)
        await state.update_data({"selected_year": currect_year, "selected_month": currect_month, "selected_day": currect_day})

@router.callback_query(
        ActivateSending.choosing_media_group,
        ConfirmingCallback.filter(
            F.action == "schedule"
        )
)
async def schedule_mailing(
        call: types.CallbackQuery, state: FSMContext):
        calendar_obj = Calendar()
        date = datetime.datetime.now(tz=ZoneInfo("Europe/Kiev"))
        currect_year = date.year
        currect_month = date.month
        currect_day = date.day
        await call.message.edit_text(text="Выберите нужную дату и напишите желаемое время", reply_markup=calendar_obj.generate_calendar(currect_year, currect_month, currect_year, currect_month, currect_day, "group"))
        await state.set_state(ActivateSending.schedule_group)
        await state.update_data({"selected_year": currect_year, "selected_month": currect_month, "selected_day": currect_day})


@router.callback_query(CalendarData.filter(F.day),  ActivateSending.schedule_group)
async def group_process_day_choice(call: types.CallbackQuery, callback_data: CalendarData, state: FSMContext):
    calendar_obj = Calendar()
    year, month, day = callback_data.year, callback_data.month, callback_data.day
    await call.message.edit_reply_markup(reply_markup=calendar_obj.generate_calendar(year, month, year, month, day, 'group'))
    await state.update_data({"selected_year": year, "selected_month": month, "selected_day": day})
    return True


@router.callback_query(CalendarData.filter(F.day), ActivateSending.schedule)
async def process_day_choice(call: types.CallbackQuery, callback_data: CalendarData, state: FSMContext):
    calendar_obj = Calendar()
    year, month, day = callback_data.year, callback_data.month, callback_data.day
    await call.message.edit_reply_markup(reply_markup=calendar_obj.generate_calendar(year, month, year, month, day, 'default'))
    await state.update_data({"selected_year": year, "selected_month": month, "selected_day": day})
    return True


@router.callback_query(
        ActivateSending.choosing_media_group,
        ConfirmingCallback.filter(
            F.action == "schedule"
        )
)
async def schedule_mailing_group(
        call: types.CallbackQuery, state: FSMContext):
        calendar_obj = Calendar()
        date = datetime.datetime.now(tz=ZoneInfo("Europe/Kiev"))
        currect_year = date.year
        currect_month = date.month
        currect_day = date.day
        await call.message.edit_text(text="Выберите нужную дату и напишите желаемое время", reply_markup=calendar_obj.generate_calendar(currect_year, currect_month, currect_year, currect_month, currect_day, "group"))
        await state.set_state(ActivateSending.schedule_group)
        await state.update_data({"selected_year": currect_year, "selected_month": currect_month, "selected_day": currect_day})


@router.callback_query(CalendarData.filter(F.action == "next_month"), StateFilter(ActivateSending.schedule, ActivateSending.schedule_group))
async def process_month_switch(call: types.CallbackQuery, callback_data: CalendarData, state: FSMContext):
    calendar_obj = Calendar()
    month = callback_data.month
    year = callback_data.year
    data = await state.get_data()
    selected_year, selected_month, selected_day = data.get("selected_year"), data.get("selected_month"), data.get("selected_day")
    if month == 12:
        year += 1
        month = 0
    month += 1
    await call.message.edit_reply_markup(reply_markup=calendar_obj.generate_calendar(year, month, selected_year, selected_month, selected_day, 'default'))
    return True


@router.callback_query(CalendarData.filter(F.action == "prev_month"), StateFilter(ActivateSending.schedule, ActivateSending.schedule_group))
async def process_month_switch(call: types.CallbackQuery, callback_data: CalendarData, state: FSMContext):
    calendar_obj = Calendar()
    month = callback_data.month
    year = callback_data.year
    data = await state.get_data()
    selected_year, selected_month, selected_day = data.get("selected_year"), data.get("selected_month"), data.get("selected_day")
    if datetime.datetime.now(tz=ZoneInfo("Europe/Kiev")).month == month and datetime.datetime.now(tz=ZoneInfo("Europe/Kiev")).year == year:
        await call.answer("Месяц не может быть меньше нынешнего.")
        return
    if month == 1:
        year -= 1
        month = 12
        await call.message.edit_reply_markup(reply_markup=calendar_obj.generate_calendar(year, month, selected_year, selected_month, selected_day, 'default'))
        return True
    month -= 1
    await call.message.edit_reply_markup(reply_markup=calendar_obj.generate_calendar(year, month, selected_year, selected_month, selected_day, 'default'))
    return True

@router.message(F.text.regexp("([01]\d|2[0-3]):([0-5]\d)").as_("time"), ActivateSending.schedule)
async def schedule_msg(message: types.Message, time: re.Match[str], state: FSMContext, scheduler: ContextSchedulerDecorator):
    data = await state.get_data()
    hour, minute = time.groups()
    year, month, day = data.get("selected_year"), data.get("selected_month"), data.get("selected_day")
    run_date = datetime.datetime(year=year, month=month, day=day, hour=int(hour), minute=int(minute), second=0, tzinfo=ZoneInfo("Europe/Kyiv"))
    if datetime.datetime.now(tz=ZoneInfo("Europe/Kiev")) >= run_date:
        await message.answer("Нельзя запланировать раньше нынешнего времени") 
        return
    from_chat_id = message.from_user.id
    sch = scheduler.add_job(schedule_mail, 'date', run_date=run_date, kwargs={"data": data, "from_chat_id": from_chat_id})
    selected_year, selected_month, selected_day = data.get("selected_year"), data.get("selected_month"), data.get("selected_day")
    await message.answer("Рассылка была успешно запланирована! \nId рассылки: <code>{}</code>\nВыбранное время: {}\nВыбранная дата: {}-{}-{}".format(sch.id, time.string, selected_year, selected_month, selected_day), parse_mode="html")
    await state.clear()
    return True


@router.message(F.text.regexp("([01]\d|2[0-3]):([0-5]\d)").as_("time"), ActivateSending.schedule_group)
async def schedule_group(message: types.Message, time: re.Match[str], state: FSMContext, scheduler: ContextSchedulerDecorator):
    data = await state.get_data()
    hour, minute = time.groups()
    year, month, day = data.get("selected_year"), data.get("selected_month"), data.get("selected_day")
    run_date = datetime.datetime(year=year, month=month, day=day, hour=int(hour), minute=int(minute), second=0, tzinfo=ZoneInfo("Europe/Kyiv"))
    if datetime.datetime.now(tz=ZoneInfo("Europe/Kiev")) >= run_date:
        await message.answer("Нельзя запланировать раньше нынешнего времени") 
        return
    from_chat_id = message.from_user.id
    sch = scheduler.add_job(schedule_mail_group, 'date', run_date=run_date, kwargs={"data": data, "from_chat_id": from_chat_id})
    selected_year, selected_month, selected_day = data.get("selected_year"), data.get("selected_month"), data.get("selected_day")
    await message.answer("Рассылка была успешно запланирована! \nId рассылки: <code>{}</code>\nВыбранное время: {}\nВыбранная дата: {}-{}-{}".format(sch.id, time.string, selected_year, selected_month, selected_day), parse_mode="html")
    await state.clear()
    return True


@router.callback_query(
    ActivateSending.choosing,
    ConfirmingCallback.filter(  
        F.action == "sure"
    )
)
async def sending_func(
        call: types.CallbackQuery,
        state: FSMContext,
        db: DbRepo,
        bot: Bot
):
    data = await state.get_data()
    message_id = data.get("msg_id")
    reply_markup = data.get("reply_markup")
    await call.message.edit_text(
        text="Рассылка начнется через несколько секунд.",
        reply_markup=stop_mailing()
    )
    mailing = Mailing()
    users = await db.user.get_all_ids()
    admins = await db.user.get_admin_ids()
    all_us = admins + users

    asyncio.create_task(mailing.copy_sending(
        users=all_us,
        bot=bot,
        message_id=message_id,
        from_chat_id=call.from_user.id,
        notif_msg_id=call.message.message_id,
        reply_markup=reply_markup
    ))
    await call.message.edit_text("<i>Рассылка успешно начата. \nРассылку получат: {} пользователей</i>".format(len(users)), parse_mode="html", reply_markup=stop_mailing())
    await state.clear()


@router.callback_query(
    ConfirmingCallback.filter(
        F.action == "stop"
    )
)
async def stop_mailing_button(
        call: types.CallbackQuery,
        state: FSMContext
):
    await state.clear()
    await call.message.edit_text(
        "Рассылка успешно отменена!",
        reply_markup=back_button())
    exit()
