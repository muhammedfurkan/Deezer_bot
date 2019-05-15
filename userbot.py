import asyncio
from time import time
import shutil
from functools import partial
from concurrent import futures
from multiprocessing import Process


import pyrogram

import config
import db_utils
from bot import bot
from var import var


loop = asyncio.get_event_loop()


async def start():
    global client
    client = pyrogram.Client(
        'DeezerMusicBot', api_id=config.client_api_id,
        api_hash=config.client_api_hash, bot_token=config.bot_token)
    await client.start()


async def post_large_track(path, track, quality='mp3', provider='deezer'):
    if provider == 'deezer':
        msg = await client.send_audio(
            chat_id=-1001246220493, audio=path, duration=track.duration,
            title=track.title, performer=track.artist.name)
        await db_utils.add_track(track.id, msg.audio.file_id, quality)
    elif provider == 'soundcloud':
        msg = await client.send_audio(
            chat_id=-1001246220493, audio=path, duration=track.duration,
            title=track.title, performer=track.artist)
        await db_utils.add_sc_track(track.id, msg.audio.file_id)


loop.run_until_complete(start())
