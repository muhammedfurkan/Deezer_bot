from math import ceil

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from yarl import URL
from utils import new_callback


def soundcloud_keyboard(results, page, per_page=5):
    kb = InlineKeyboardMarkup(2)
    total_pages = ceil(len(results) / per_page)
    start = (page-1) * per_page
    stop = start + per_page
    last_page = page == total_pages
    for i, result in enumerate(results[start : stop], start=start):
        kb.insert(InlineKeyboardButton(
            f'{i+1}. {result.user.username} - {result.title}',
            callback_data=new_callback('sc_track', result.id, 'send')))
        kb.row()
    if page != 1:
        kb.insert(InlineKeyboardButton(
            '◀️', callback_data=new_callback('sc_page', page-1)))
    if not last_page:
        kb.insert(InlineKeyboardButton(
            '️️▶️', callback_data=new_callback('sc_page', page+1)))
    return kb


def large_file_keyboard():
    kb = InlineKeyboardMarkup(1)
    kb.insert(InlineKeyboardButton(
        "File is too big, Telegram won't let to upload it",
        callback_data='big_file'))
    return kb


def quality_settings_keyboard(current_setting):
    kb = InlineKeyboardMarkup(2)
    mp3 = ' (current)' if current_setting == 'mp3' else ''
    flac = ' (current)' if current_setting == 'flac' else ''
    kb.insert(InlineKeyboardButton(
        "MP3 320" + mp3,
        callback_data='quality:mp3'))
    kb.insert(InlineKeyboardButton(
        "FLAC" + flac,
        callback_data='quality:flac'))
    return kb


def finish_download_keyboard(track_id):
    kb = InlineKeyboardMarkup(1)
    kb.insert(InlineKeyboardButton(
        'Loading full track, please wait...', callback_data='finish_download'))
    return kb


def start_keyboard():
    kb = InlineKeyboardMarkup(1)
    kb.insert(InlineKeyboardButton('Search', switch_inline_query_current_chat=''))
    kb.insert(InlineKeyboardButton('Search albums', switch_inline_query_current_chat='.a '))
    kb.insert(InlineKeyboardButton('Search artists', switch_inline_query_current_chat='.ar '))
    return kb


def search_results_keyboard(results, page, per_page=5):
    kb = InlineKeyboardMarkup(2)
    total_pages = ceil(len(results) / per_page)
    start = (page-1) * per_page
    stop = start + per_page
    last_page = page == total_pages
    for i, result in enumerate(results[start : stop], start=start):
        kb.insert(InlineKeyboardButton(
            f'{i+1}. {result.artist.name} - {result.title}',
            callback_data=new_callback('track', result.id, 'send')))
        kb.row()
    if page != 1:
        kb.insert(InlineKeyboardButton(
            '◀️', callback_data=new_callback('page', page-1)))
    if not last_page:
        kb.insert(InlineKeyboardButton(
            '️️▶️', callback_data=new_callback('page', page+1)))
    return kb


def stats_keyboard():
    kb = InlineKeyboardMarkup()
    kb.insert(InlineKeyboardButton('Update', callback_data='stats'))
    return kb


def today_stats_keyboard():
    kb = InlineKeyboardMarkup()
    kb.insert(InlineKeyboardButton('Update', callback_data='today'))
    return kb


def artist_keyboard(artist):
    kb = InlineKeyboardMarkup(2)
    kb.insert(InlineKeyboardButton('Top 5 Tracks', callback_data=new_callback('artist', artist.id, 'top5')))
    kb.insert(InlineKeyboardButton('Albums', callback_data=new_callback('artist', artist.id, 'albums')))
    kb.insert(InlineKeyboardButton('Related artists', callback_data=new_callback('artist', artist.id, 'related')))
    kb.insert(InlineKeyboardButton('Radio', callback_data=new_callback('artist', artist.id, 'top5')))
    kb.insert(InlineKeyboardButton('Wikipedia', callback_data=new_callback('artist', artist.id, 'wiki')))
    kb.insert(InlineKeyboardButton('Search on Last.Fm', url=str(URL(f'https://www.last.fm/search?q={artist.name}'))))
    return kb


def related_artists_keyboard(related, main_artist_id):
    kb = InlineKeyboardMarkup(1)
    for i, artist in enumerate(related[:10], start=1):
        kb.insert(InlineKeyboardButton(f'{i}. {artist.name}', callback_data=new_callback('artist', artist.id, 'send')))
    kb.insert(InlineKeyboardButton('Go back', callback_data=new_callback('artist', main_artist_id, 'main')))
    return kb


def artist_radio_keyboard(radio, artist_id):
    kb = InlineKeyboardMarkup(1)
    for i, track in enumerate(radio, start=1):
        kb.insert(InlineKeyboardButton(f'{i}. {track.artist.name} \u2013 {track.title}', callback_data=new_callback('track', track.id, 'send')))
    kb.insert(InlineKeyboardButton('Go back', callback_data=new_callback('artist', artist_id, 'main')))
    return kb

def album_keyboard(album, tracks, post=False):
    kb = InlineKeyboardMarkup(1)
    for i, track in enumerate(tracks, start=1):
        kb.insert(InlineKeyboardButton(f'{i}. {track.title}', callback_data=new_callback('track', track.id, 'send')))
    kb.insert(InlineKeyboardButton('Get all tracks', callback_data=new_callback('album', album.id, 'download')))
    if post:
        kb.insert(InlineKeyboardButton('Post', callback_data=new_callback('album', album.id, 'post')))
    return kb


def albums_keyboard(artist, albums):
    kb = InlineKeyboardMarkup(1)
    for album in albums:
        year = album.release_date.split('-')[0]
        kb.insert(InlineKeyboardButton(f'{album.title} ({year})', callback_data=new_callback('album', album.id, 'send')))
    kb.insert(InlineKeyboardButton('Go back', callback_data=new_callback('artist', artist.id, 'main')))
    return kb


def top5_keyboard(artist, top):
    kb = InlineKeyboardMarkup(1)
    for i, track in enumerate(top, start=1):
        kb.insert(InlineKeyboardButton(f'{i}. {track.title}', callback_data=new_callback('track', track.id, 'send')))
    kb.insert(InlineKeyboardButton('Go back', callback_data=new_callback('artist', artist.id, 'main')))     
    return kb
