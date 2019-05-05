#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from contextlib import suppress
import asyncio
import shutil
import re
from sys import argv

from aiogram.utils import executor
from aiogram import types
from aiohttp import ClientSession

from bot import bot, dp, register_handlers
from var import var
import handlers
import inline_handlers
import callback_handlers
import filters
from logger import update_logging_files

loop = asyncio.get_event_loop()


async def close():
    var.db.commit()
    var.db.close()
    var.conn.close()
    logging.cancel()
    await var.session.close()


if __name__ == '__main__':
    with suppress(FileNotFoundError):
        shutil.rmtree('downloads')
    register_handlers(dp, handlers, inline_handlers, callback_handlers)
    logging = asyncio.ensure_future(update_logging_files())
    executor.start_polling(dp, loop=loop)
    loop.run_until_complete(close())
    loop.close()
