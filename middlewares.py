from asyncio import sleep

from aiogram.dispatcher.middlewares import BaseMiddleware

import deezer_api
from var import var
from logger import message_logger, format_name

class Middleware(BaseMiddleware):
    async def on_process_message(self, message, data):
        message_logger.info(
            f'[message from {format_name(message.from_user)}] {message.text}')
