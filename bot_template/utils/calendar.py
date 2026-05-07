import calendar
import datetime
from zoneinfo import ZoneInfo

from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot_template.handlers.callback.confirming_sending import CalendarData


class Calendar:

    def generate_calendar(self, year, month, selected_year, selected_month, selected_day, type: str):
        self.current_year = year
        self.current_month = month
        cal = calendar.monthcalendar(year, month)
        month_markup = InlineKeyboardBuilder()
        month_markup.add(*[types.InlineKeyboardButton(text='◀️', 
                                                      callback_data=CalendarData(
                                                                                action="prev_month", 
                                                                                year=year, 
                                                                                month=month).pack()
                                                                                ),
                           types.InlineKeyboardButton(text=f"{self.get_month_name(month)}, {year}", 
                                                    callback_data='ignore'),
                           types.InlineKeyboardButton(text='▶️', 
                                                    callback_data=CalendarData(
                                                                               action="next_month", 
                                                                               year=year, 
                                                                               month=month).pack()
                                                                              )
                          ]
                        )
        
        date = datetime.datetime.now(tz=ZoneInfo("Europe/Kiev"))
        currect_year = date.year
        currect_month = date.month
        currect_day = date.day
        currect_date = date.date()
        for week in cal:
            if (currect_month == month and currect_year == year and currect_day > week[6] and week[6] != 0):
                pass
            else:
                for day in week:
                    if day == 0 or (currect_date > datetime.date(year, month, day)):
                        month_markup.button(
                        text='•',
                        callback_data="ignore"
                    )
                    elif (datetime.date(selected_year, selected_month, selected_day) == datetime.date(year, month, day)):
                        month_markup.button(
                            text="✅ {}".format(day),
                            callback_data=CalendarData(
                            year=year,
                            month=month,
                            day=day
                            ).pack()
                        )
                    else:
                        month_markup.button(
                            text=str(day),
                            callback_data=CalendarData(
                            year=year,
                            month=month,
                            day=day
                            ).pack()
                        )
        month_markup.button(text="назад", callback_data=f"{type}")
        month_markup.adjust(3, 7)
        return month_markup.as_markup()
    
    @staticmethod
    def get_month_name(month):
        month_names = [
            'янв.', 'февр.', 'март', 'апр.',
            'май', 'июнь', 'июль', 'авг.',
            'сент.', 'окт.', 'нояб.', 'дек.'
        ]
        return month_names[month - 1]