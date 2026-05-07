__all__ = ["setup_commands_routers", "setup_join_requests_routers",
           "setup_callback_routers", "setup_my_chat_member_routers"]

from bot_template.handlers.commands import setup_commands_routers
from bot_template.handlers.join_requests import setup_join_requests_routers
from bot_template.handlers.callback import setup_callback_routers
from bot_template.handlers.my_chat_member import setup_my_chat_member_routers