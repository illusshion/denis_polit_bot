from aiogram.filters.state import State, StatesGroup


class MenuState(StatesGroup):
    main_menu = State()


class SettingsState(StatesGroup):
    settings_menu = State()
    add_admin_state = State()
    delete_admin_state = State()
    change_captcha = State()
    send_captcha = State()
    accept_requests_state = State()
    reject_requests_state = State()
