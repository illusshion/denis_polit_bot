from aiogram import Router, types
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext

from bot_template.keyboard.inline_keyboards import create_menu_keyboard
from bot_template.states import MenuState

router = Router()


@router.message(
    Command("menu"),
    StateFilter("*")
)
async def start_cmd(
        message: types.Message,
        state: FSMContext
):
    await message.reply(
        text="Приветствую! Выбери нужную тебе функцию.",
        reply_markup=create_menu_keyboard()
    )
    await state.set_state(MenuState.main_menu)
