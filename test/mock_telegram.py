"""mocks for Telegram"""

from unittest.mock import MagicMock

class Bot:
    def __init__(self, token, **_):
        self.posts = []

    def get_me(self, **_):
        pass

    def sendMessage(self, chat_id, text, parse_mode=None, **_):
        self.posts.append(text)

error = MagicMock(TelegramError=MagicMock())
ParseMode = MagicMock(HTML=MagicMock())
