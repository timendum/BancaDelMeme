"""mocks for Telegram"""
from unittest.mock import MagicMock

import telegram as _telegram


class Bot:
    def __init__(self, token, **_):
        self.posts = []

    def get_me(self, **_):
        pass

    def sendMessage(self, chat_id, text, parse_mode=None, **_):
        self.posts.append(text)
        return MagicMock(message_id=1)


error = _telegram.error
ParseMode = _telegram.ParseMode
