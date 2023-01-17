"""mocks for Telegram"""
from unittest.mock import MagicMock

import telegram as _telegram

posts = []
deleted = []

class Bot:
    def __init__(self, token, **_):
        pass

    async def get_me(self, **_):
        return None

    async def send_message(self, chat_id, text, parse_mode=None, **_):
        posts.append(text)
        return MagicMock(message_id=1)

    async def delete_message(self, chat_id, message_id):
        deleted.append(message_id)
        return None

error = _telegram.error
constants = _telegram.constants
