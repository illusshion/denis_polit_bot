from aiogram.filters.state import StatesGroup, State


class ActivateSending(StatesGroup):
    writing = State()
    choosing = State()
    choosing_media_group = State()
    add_button = State()
    sending = State()
    schedule = State()
    schedule_group = State()
