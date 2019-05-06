#!/usr/bin/env python
# -*- coding: utf-8 -*-
import asyncio
import re
from sys import argv

import aiohttp
import aioredis
from aiogram import Bot, types
from aiogram.utils.callback_data import CallbackData
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import Dispatcher

import config
import utils
from filters import filters
from middlewares import Middleware
from sql import database
from var import var

loop = asyncio.get_event_loop()

bot = Bot(token=config.bot_token, loop=loop)
storage = MemoryStorage()
var.downloading = {}


def register_handlers(dp, handlers, inline_handlers, callback_handlers):
    spotify_playlist = re.compile(r'.+spotify.com/.+/playlist/.+')

    if '-a' in argv:
        dp.register_message_handler(handlers.only_admin_handler)
    dp.register_message_handler(
        handlers.audio_file_handler,
        content_types=[types.ContentType.AUDIO])
    # SoundCloud
    dp.register_message_handler(
        handlers.soundcloud_handler,
        commands=['sc'])
    dp.register_message_handler(
        handlers.soundcloud_link_handler,
        lambda m: 'soundcloud.com' in m.text)
    dp.register_callback_query_handler(
        callback_handlers.soundcloud_handler,
        lambda c: c.data.startswith('sc_'))
    dp.register_message_handler(handlers.start_command_handler, commands=['start'])
    dp.register_message_handler(handlers.quality_setting_handler, commands=['quality'])
    dp.register_message_handler(
        handlers.getstats_handler, commands=['stats'])	
    dp.register_message_handler(
        handlers.today_stats_handler, commands=['today'])	
    dp.register_message_handler(
        handlers.redownload_handler, commands=['re', 'redownload'])
    dp.register_message_handler(
        handlers.post_to_channel_handler,
        lambda m: m.chat.id in config.admins, commands=['post'])
    dp.register_message_handler(
        handlers.artist_search_handler, commands=['a', 'artist'])
    dp.register_message_handler(handlers.diskography_handler, commands=['d'])
    dp.register_message_handler(
        handlers.spotify_album_handler,
        lambda m: 'open.spotify.com/album' in m.text)
    dp.register_message_handler(
        handlers.spotify_artist_handler, lambda m: 'open.spotify.com/artist' in m.text)
    dp.register_message_handler(
        handlers.spotify_playlist_handler,
        lambda m: re.match(spotify_playlist, m.text))
    dp.register_message_handler(
        handlers.spotify_handler,
        lambda m: 'open.spotify.com/track' in m.text)
    dp.register_message_handler(
        handlers.artist_handler,
        lambda m: '/artist/' in m.text)
    dp.register_message_handler(
        handlers.album_handler,
        lambda m: '/album/' in m.text)
    dp.register_message_handler(
        handlers.cache_playlist,
        lambda m: '/playlist/' in m.text and '/c ' in m.text)
    dp.register_message_handler(
        handlers.playlist_handler,
        lambda m: '/playlist/' in m.text)
    dp.register_message_handler(
        handlers.track_handler, 
        lambda m: '/track/' in m.text)
    dp.register_message_handler(
        handlers.search_handler, lambda m: m.chat.type == 'private')
    dp.register_inline_handler(
        inline_handlers.artist_search_inline_handler,
        lambda q: '.ar' in q.query)
    dp.register_inline_handler(inline_handlers.inline_handler)
    dp.register_callback_query_handler(
        callback_handlers.quality_setting_hanlder,
        lambda d: d.data.startswith('quality'))
    dp.register_callback_query_handler(
        callback_handlers.finish_download_handler,
        lambda d: d.data == 'finish_download')
    dp.register_callback_query_handler(
        callback_handlers.large_file_handler,
        lambda d: 'big_file' in d.data)
    dp.register_callback_query_handler(
        callback_handlers.pages_handler,
        lambda d: 'page' in d.data)
    dp.register_callback_query_handler(
        callback_handlers.stats_callback_handler,
        lambda d: d.data == 'stats')
    dp.register_callback_query_handler(
        callback_handlers.today_stats_callback_handler,
        lambda d: d.data == 'today')
    dp.register_callback_query_handler(
        callback_handlers.artist_callback_handler,
        lambda d: 'artist' in d.data)
    dp.register_callback_query_handler(callback_handlers.callback_handler)
    dp.register_chosen_inline_handler(inline_handlers.finish_download_handler)
    dp.middleware.setup(Middleware())


try:
    global session
    cookies = {'arl':  config.deezer_arl_cookie}
    headers = {
        'user-agent':      ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                            'AppleWebKit/537.36 (KHTML, like Gecko) '
                            'Chrome/72.0.3626.121 Safari/537.36'),
        'Content-Language': 'en-US',
        'Cache-control':   'max-age=0',
        'Accept-Language': 'en-US,en;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept-Charset':  'utf-8,ISO-8859-1;q=0.8,*;q=0.7',
        # 'content-type':    'application/json;text/plain;charset=UTF-8',
        'Connection': 'keep-alive',
    }

    var.session = aiohttp.ClientSession(
        cookies=cookies, headers=headers, raise_for_status=False)
    var.session.get = utils.retry(
        aiohttp.ClientResponseError, retries=5, cooldown=0.1)(var.session.get)
    var.session.post = utils.retry(
        aiohttp.ClientResponseError, retries=5, cooldown=0.1)(var.session.post)
    print('created session')
    var.CSRFToken = None
    var.loop = loop

    dp = Dispatcher(bot, storage=storage)
    from spotify import Spotify_API
    var.spot = Spotify_API(
            config.spotify_client, config.spotify_secret)
    var.db = database('db.sqlite')
    var.conn = loop.run_until_complete(aioredis.create_connection(
            ('localhost', 6379), encoding='utf-8', db=4, loop=loop))
    print('datebase connected')
    
except Exception as e:
    print(e)
