from typing import Optional
from aiogram.filters.callback_data import CallbackData


class ConfirmingCallback(CallbackData, prefix="sending"):
    action: str

class CalendarData(CallbackData, prefix="cal"):
    action: Optional[str] = None
    year: int
    month: int
    day: Optional[int] = None