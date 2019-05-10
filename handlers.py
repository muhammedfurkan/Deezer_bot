import re
from asyncio import sleep
from glob import iglob
from datetime import date

from aiogram import types
from aiogram.dispatcher.handler import SkipHandler

from var import var
from bot import bot
import utils
import db_utils
import inline_keyboards
import deezer_api
import soundcloud_api
import config
import methods
from logger import error_logger


async def only_admin_handler(message: types.Message):
    if message.chat.id in config.admins:
        raise SkipHandler()


async def quality_setting_handler(message: types.Message):
    if message.chat.id in config.admins:
        current_setting = await db_utils.get_quality_setting(message.chat.id)
        return await bot.send_message(
            message.chat.id, 'Select quality',
            reply_markup=inline_keyboards.quality_settings_keyboard(current_setting))


async def soundcloud_link_handler(message: types.Message):
    url = utils.clear_link(message)
    result = await soundcloud_api.resolve(url)
    if result.kind == 'track':
        await methods.send_soundcloud_track(message.chat.id, result)
    elif result.kind == 'user':
        await methods.send_soundcloud_artist(message.chat.id, result)
    elif result.kind == 'playlist':
        await methods.send_soundcloud_playlist(message.chat.id, result)



async def audio_file_handler(message: types.Message):
    if message.caption and message.chat.id in config.admins:
        await db_utils.add_track(int(message.caption), message.audio.file_id)
    else:
        print(message.audio.file_id)


async def start_command_handler(message: types.Message):
    db_utils.add_user(message.from_user)
    await bot.send_message(
        chat_id=message.chat.id,
        text=config.start_message,
        disable_web_page_preview=True,
        parse_mode=types.ParseMode.MARKDOWN,
        reply_markup=inline_keyboards.start_keyboard)


async def getstats_handler(message):
    sc_tracks_count = await var.conn.execute('get', 'tracks:soundcloud:total')
    dz_tracks_count = await var.conn.execute('get', 'tracks:deezer:total')
    all_users_count = db_utils.get_users_count()
    await bot.send_message(
        chat_id=message.chat.id,
        text=f'users: {all_users_count}\n\n'
            f'Deezer tracks: {dz_tracks_count}\n\nSoundCloud tracks: {sc_tracks_count}',
        reply_markup=inline_keyboards.stats_keyboard)


async def today_stats_handler(message):
    stats = utils.get_today_stats()
    await bot.send_message(
        chat_id=message.chat.id,
        text=f'Downloaded tracks: {stats.downloaded_tracks}\n\n'
        f'Sent tracks: {stats.sent_tracks}\n\n'
        f'Received messages: {stats.received_messages}',
        reply_markup=inline_keyboards.today_stats_keyboard)


async def redownload_handler(message: types.Message):
    if 'com/' in message.text:
        obj_type = message.text.split('/')[-2]
        obj_id = message.text.split('/')[-1]
        if obj_type == 'track':
            track = await deezer_api.gettrack(obj_id)
            await methods.send_track(track, message.chat, Redownload=True)
        else:
            album = await deezer_api.getalbum(obj_id)
            for track in await album.get_tracks():
                await methods.send_track(track, message.chat, Redownload=True)
    else:
        search = await deezer_api.search(q=message.text.strip('/re '))
        await methods.send_track(await deezer_api.gettrack(search[0].id), message.chat, Redownload=True)


async def diskography_handler(message: types.Message):
    if message.reply_to_message and message.reply_to_message.audio:
        artist_name = message.reply_to_message.audio.performer
    else:
        artist_name = message.text.strip('/d ').split('/')[-1]
    if artist_name.isdigit():
        artist = await deezer_api.getartist(artist_name)
    else:
        artist = (await deezer_api.search('artist', artist_name))[0]

    tracks = await artist.all_tracks()
    total, skipped = len(tracks), 0
    for track in tracks:
        if await db_utils.get_track(track.id):
            skipped += 1

    text = f'{artist.name}\n\nskipped ({skipped}/{total})'

    await bot.send_message(message.chat.id, text)

    for track in tracks:
        try:
            await methods.cache(track)
            await sleep(0)
        except Exception as e:
            print(e)
            await bot.send_message(message.chat.id, e)
    await bot.send_message(message.chat.id, f'{artist.name} done')

    for artist in (await artist.related())[:5]:
        try:
            await sleep(2)
            tracks = await artist.all_tracks()
            total, skipped = len(tracks), 0
            for i, track in enumerate(tracks, start=1):
                if await db_utils.get_track(track.id):
                    skipped += 1
            if skipped == total:
                await sleep(3)
                continue
            text = f'{artist.name}\n\nskipped ({skipped}/{total})'
            await bot.send_message(message.chat.id, text)
            for track in tracks:
                await methods.cache(track)
            await bot.send_message(message.chat.id, f'{artist.name} done')

        except Exception as e:
            print(e)
            await bot.send_message(message.chat.id, f'{artist.name}\n\n{e}')


async def artist_search_handler(message):
    artist = (await deezer_api.search(
        'artist', message.text.strip(message.get_command())))[0]
    await methods.send_artist(artist, message.chat.id)


async def post_to_channel_handler(message):
    album = await deezer_api.getalbum(message.text.split('/')[-1])
    chat = await bot.get_chat(-1001171972924)
    await methods.send_album(album, chat, send_all=True)
    await bot.send_message(140999479, 'done')


async def spotify_handler(message):
    spotify_song = await var.spot.get_track(message.text)
    search_query = '%s %s' % (
        spotify_song.artists[0].name,
        re.match(r'[^\(\[\-]+', spotify_song.name).group(0))
    search_results = await deezer_api.search(q=search_query)
    if not search_results:
        return await bot.send_message(
            message.chat.id, 'Sorry, track is not found on Deezer')
    await methods.send_track(search_results[0], message.chat)


async def spotify_playlist_handler(message):
    spotify_playlist = await var.spot.get_playlist(message.text)
    for track in spotify_playlist:
        try:
            search_query = '{} {}'.format(
                track.artists[0].name, re.match(r'[^\(\[\-]+', track.name).group(0))
            search_results = await deezer_api.search(q=search_query)
            if search_results:
                await methods.send_track(search_results[0], message.chat)
            else:
                await bot.send_message(
                    chat_id=message.chat.id,
                    text=f'Sorry, track {track.artists[0].name} - {track.name} is not found on Deezer')
        except Exception as e:
            print(e)
        await sleep(.5)


async def spotify_album_handler(message):
    spotify_album = await var.spot.get_album(message.text)
    search_results = await deezer_api.search(
        'album', f'{spotify_album.artists[0].name} {spotify_album.name}')
    if not search_results:
        return await bot.send_message(
            chat_id=message.chat.id,
            text=f'Sorry, album {spotify_album.name} by {spotify_album.artists[0].name} is not found on Deezer')
    await methods.send_album(search_results[0], message.chat)


async def spotify_artist_handler(message):
    spotify_artist = await var.spot.get_artist(message.text)
    search_results = await deezer_api.search('artist', spotify_artist.name)
    await methods.send_artist(search_results[0], message.chat.id)


async def artist_handler(message):
    artist = await deezer_api.getartist(message.text.split('/')[-1])
    await methods.send_artist(artist, message.chat.id)


async def album_handler(message):
    album = await deezer_api.getalbum(message.text.split('/')[-1])
    await methods.send_album(album, message.chat)


async def playlist_handler(message):
    tracks = await deezer_api.getplaylist(message.text.split('/')[-1])

    for track in tracks:
        try:
            await methods.send_track(track, message.chat)
            await sleep(.02)
        except Exception as e:
            print(type(e), e)
    await bot.send_message(message.chat.id, 'playlist done')


async def cache_playlist(message):
    tracks = await deezer_api.getplaylist(message.text.split('/')[-1])
    for track in tracks:
        if not await db_utils.get_track(track.id):
            await methods.send_track(track, message.chat)
            await sleep(.01)
    await bot.send_message(message.chat.id, 'playlist cached')


async def track_handler(message):
    track = await deezer_api.gettrack(message.text.split('/')[-1])
    if utils.already_downloading(track.id):
        return
    await methods.send_track(track, message.chat)
    db_utils.add_user(message.from_user)


async def search_handler(message):
    search_results = await deezer_api.search(q=message.text)
    if not len(search_results):
        return await bot.send_message(message.chat.id, 'Nothing was found')

    await bot.send_message(
        chat_id=message.chat.id,
        text=message.text + ':',
        reply_markup=inline_keyboards.search_results_keyboard(search_results, 1))
    db_utils.add_user(message.from_user)
