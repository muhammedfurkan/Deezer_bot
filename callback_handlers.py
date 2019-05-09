from contextlib import suppress

from aiogram import exceptions, types

from bot import bot
import utils
import db_utils
import methods
import inline_keyboards
import deezer_api
import soundcloud_api
from var import var
from utils import parse_callback


async def soundcloud_handler(callback):
    await callback.answer()
    track_id = callback.data.split(':')[1]
    track = await soundcloud_api.get_track(track_id)
    await methods.send_soundcloud_track(callback.message.chat.id, track)


async def finish_download_handler(data):
    await data.answer('please wait, downloading track...', show_alert=True)


async def large_file_handler(callback):
    await callback.answer('Track is too large, Telegram won\'t let to upload it', show_alert=True)


async def quality_setting_hanlder(callback):
    _, setting = parse_callback(callback.data)
    await db_utils.set_quality_setting(callback.from_user.id, setting)
    await callback.answer(f'quality set to {setting}')
    with suppress(exceptions.MessageNotModified):
        await bot.edit_message_reply_markup(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            reply_markup=inline_keyboards.quality_settings_keyboard(setting))


async def pages_handler(callback):
    await callback.answer()
    mode, page = parse_callback(callback.data)
    q = callback.message.text[:-1]
    with suppress(exceptions.MessageNotModified):
        if mode == 'page':
            search_results = await deezer_api.search(q=q)
            await bot.edit_message_reply_markup(
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                reply_markup=inline_keyboards.search_results_keyboard(search_results, int(page)))
        elif mode == 'sc_page':
            search_results = await soundcloud_api.search(q=q)
            await bot.edit_message_reply_markup(
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                reply_markup=inline_keyboards.sc_search_results_keyboard(search_results, int(page)))


async def stats_callback_handler(callback):
    await callback.answer()
    sc_tracks_count = await var.conn.execute('get', 'tracks:soundcloud:total')
    dz_tracks_count = await var.conn.execute('get', 'tracks:deezer:total')
    all_users_count = db_utils.get_users_count()
    with suppress(exceptions.MessageNotModified):
        await bot.edit_message_text(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=f'users: {all_users_count}\n\n'
                f'Deezer tracks: {dz_tracks_count}\n\nSoundCloud tracks: {sc_tracks_count}',
            reply_markup=inline_keyboards.stats_keyboard)


async def today_stats_callback_handler(callback):
    await callback.answer()
    stats = utils.get_today_stats()
    message_text = (
        f'Downloaded tracks: {stats.downloaded_tracks}\n\n'
        f'Sent tracks: {stats.sent_tracks}\n\n'
        f'Received messages: {stats.received_messages}')
    with suppress(exceptions.MessageNotModified):
        await bot.edit_message_text(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=message_text,
            reply_markup=inline_keyboards.today_stats_keyboard)


async def artist_callback_handler(callback):
    await callback.answer()
    print(callback.data)
    if ':' in callback.data:
        mode, obj_id, method = parse_callback(callback.data)
    else:
        mode = ''
        obj_id = callback.data

    if mode == 'artist':
        artist = await deezer_api.getartist(obj_id)
        if method == 'top5':
            top = await artist.top(5)
            return await bot.edit_message_reply_markup(
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                reply_markup=inline_keyboards.top5_keyboard(artist, top))

        elif method == 'albums':
            albums = await artist.albums()
            return await bot.edit_message_reply_markup(
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                reply_markup=inline_keyboards.albums_keyboard(artist, albums))

        elif method == 'related':
            related = await artist.related()
            return await bot.edit_message_reply_markup(
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                reply_markup=inline_keyboards.related_artists_keyboard(
                    related, artist.id))

        elif method == 'radio':
            radio = await artist.radio()
            return await bot.edit_message_reply_markup(
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                reply_markup=inline_keyboards.artist_radio_keyboard(
                    radio, artist.id))

        elif method == 'main':
            kboard = inline_keyboards.artist_keyboard(artist)
            return await bot.edit_message_reply_markup(
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                reply_markup=kboard)

        elif method == 'send':
            return await bot.send_photo(
                chat_id=callback.message.chat.id,
                photo=artist.picture_xl,
                caption=f'[{artist.name}]({artist.share})',
                parse_mode='markdown',
                reply_markup=inline_keyboards.artist_keyboard(artist))

        elif method == 'wiki':
            artist = await deezer_api.getartist(obj_id)
            r = await bot.session.get(
                f'https://wikipedia.org/w/index.php?search={artist.name}')
            return await bot.send_message(
                callback.message.chat.id, r.url)


async def callback_handler(callback):
    mode, obj_id, method = parse_callback(callback.data)

    if mode == 'album':
        if method == 'download':
            await callback.answer()
            album = await deezer_api.getalbum(obj_id)
            await bot.edit_message_reply_markup(
                callback.message.chat.id,
                callback.message.message_id,
                None)
            return await methods.send_album(
                album, callback.message.chat, pic=False, send_all=True)

        elif method == 'post':
            await callback.answer()
            album = await deezer_api.getalbum(obj_id)
            chat = await bot.get_chat(-1001171972924)
            await methods.send_album(album, chat, send_all=True)

        elif method == 'send':
            await callback.answer('downloading')
            album = await deezer_api.getalbum(obj_id)
            return await methods.send_album(album, callback.message.chat)    

    elif mode == 'track_deezer':
        if utils.already_downloading(int(obj_id)):
            return await callback.answer('already downloading, please wait...')
        else:
            await callback.answer('downloading...')
            track = await deezer_api.gettrack(obj_id)
            await methods.send_track(track, callback.message.chat)

    elif mode == 'track_soundcloud':
        if utils.already_downloading(int(obj_id)):
            return await callback.answer('already downloading, please wait...')
        else:
            await callback.answer('already downloading, please wait...')
            track = await soundcloud_api.get_track(obj_id)
            await methods.send_soundcloud_track(track, callback.message.chat)
