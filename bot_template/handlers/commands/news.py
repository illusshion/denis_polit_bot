import asyncio
from typing import List, Sequence, Union
from aiogram import Bot, Router, F, types
from aiogram.types import Message, ContentType
from aiogram.filters import Command
from aiogram.filters.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select
from pydantic import parse_obj_as
import ujson as json

from bot_template.keyboard.inline_keyboards import back_button
from bot_template.handlers.commands.sending import InputMedia
from bot_template.db import News
from bot_template.handlers.callback import SettingsCallback, MenuCallback

METHODS = {
    ContentType.ANIMATION: "send_animation",
    ContentType.AUDIO: "send_audio",
    ContentType.DOCUMENT: "send_document",
    ContentType.PHOTO: "send_photo",
    ContentType.VIDEO: "send_video",
    ContentType.VIDEO_NOTE: "send_video_note",
    ContentType.STICKER: "send_sticker",
    ContentType.VOICE: "send_voice",
    'text': "send_message"}

class NewsState(StatesGroup):
    send_news = State()

def get_file_id(message: Message):
    if not message.text:
        if message.document:
            return message.document.file_id
        elif message.photo:
            return message.photo[-1].file_id
        elif message.video:
            return message.video.file_id
        elif message.voice:
            return message.voice.file_id
        elif message.audio:
            return message.audio.file_id
        elif message.video_note:
            return message.video_note.file_id
        else:
            return message.animation.file_id
    else:
        return None 

async def send_news(list_news: Sequence[News], chat_id: int, bot: Bot):
    for obj in list_news:
        if obj.format == "media_group":
            media_group_unpack = json.loads(obj.msg)
            media = parse_obj_as(List[InputMedia], media_group_unpack)
            await bot.send_media_group(chat_id=chat_id, media=media)
        elif obj.format == ContentType.TEXT:
            msg = Message.model_validate_json(obj.msg)
            await bot.send_message(chat_id, msg.html_text, reply_markup=msg.reply_markup)
        else:
            msg = Message.model_validate_json(obj.msg)
            method = getattr(bot, METHODS[obj.format], None)
            media = get_file_id(msg)
            text = msg.html_text
            await method(chat_id, media, caption=text, reply_markup=msg.reply_markup)
        await asyncio.sleep(0.5)

async def send_new(obj: News, chat_id: int, bot: Bot):
    if obj.format == "media_group":
        media_group_unpack = json.loads(obj.msg)
        media = parse_obj_as(List[InputMedia], media_group_unpack)
        await bot.send_media_group(chat_id=chat_id, media=media)
    elif obj.format == ContentType.TEXT:
        msg = Message.model_validate_json(obj.msg)
        await bot.send_message(chat_id, msg.html_text, reply_markup=msg.reply_markup)
    else:
        msg = Message.model_validate_json(obj.msg)
        method = getattr(bot, METHODS[obj.format], None)
        media = get_file_id(msg)
        text = msg.html_text
        await method(chat_id, media, caption=text, reply_markup=msg.reply_markup)

router = Router()

@router.callback_query(SettingsCallback.filter(F.action == "add_news"))
async def test(call: types.CallbackQuery, state: FSMContext):
    await state.set_state(NewsState.send_news)
    await call.message.edit_text("Отправь новости, которые нужно добавить",
                                  reply_markup=back_button())


@router.message(NewsState.send_news, F.media_group_id) 
async def news_handle(message: Message, session: AsyncSession, album: List[Message]):
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
    album = [model.model_dump() for model in group_elements]
    pack_album = json.dumps(album)

    news = News(
        msg = pack_album,
        format = "media_group"
    )
    await session.merge(news)
    await session.commit()

    await message.answer("<b>Новость успешно добавлена.</b>",
                         reply_markup=back_button())


@router.message(NewsState.send_news)
async def news_handle(message: Message, session: AsyncSession):
    news = News(
        msg = message.model_dump_json(),
        format = message.content_type
    )
    await session.merge(news)
    await session.commit()

    await message.answer("<b>Новость успешно добавлена.</b>",
                         reply_markup=back_button())

@router.message(F.text == "Новости дня")
@router.callback_query(MenuCallback.filter(F.action == "list_news"))
async def test_news(event: Union[Message, types.CallbackQuery], bot: Bot, session: AsyncSession):
    news = await session.scalars(select(News))
    result = news.all()
    if result:
        asyncio.create_task(send_news(result, event.from_user.id, bot))
    else:
        await event.answer("Новости отсутствуют!")


@router.message(F.text == "Последняя новость")
async def last_new_handle(message: Message, bot: Bot, session: AsyncSession):
    news = await session.scalars(select(News).order_by(News.id.desc()))
    result = news.first()
    if result:
        asyncio.create_task(send_new(result, message.chat.id, bot))
    else:
        await message.answer("Новости отсутствуют!")

@router.callback_query(SettingsCallback.filter(F.action == "delete_news"))
async def delete_all_news(call: types.CallbackQuery, session: AsyncSession):
    await session.execute(delete(News))
    await session.commit()
    buttons = [
        [
            types.InlineKeyboardButton(text="Добавить новости", callback_data=SettingsCallback(action="add_news").pack())
        ],
        [
            types.InlineKeyboardButton(text="Назад", callback_data=MenuCallback(action="back").pack())
        ]
    ]
    markup = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    await call.message.edit_text("Новости удалены", reply_markup=markup)