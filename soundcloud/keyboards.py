from math import ceil

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from yarl import URL

from utils import new_callback


def sc_search_results_keyboard(results, page, per_page=5):
    kb = InlineKeyboardMarkup(2)
    total_pages = ceil(len(results) / per_page)
    start = (page-1) * per_page
    stop = start + per_page
    last_page = page == total_pages
    for i, result in enumerate(results[start : stop], start=start):
        kb.insert(InlineKeyboardButton(
            f'{i+1}. {result.artist} - {result.title}',
            callback_data=new_callback('track_soundcloud', result.id, 'send')))
        kb.row()
    if page != 1:
        kb.insert(InlineKeyboardButton(
            '◀️', callback_data=new_callback('sc_page', page-1)))
    if not last_page:
        kb.insert(InlineKeyboardButton(
            '️️▶️', callback_data=new_callback('sc_page', page+1)))
    kb.row(
        InlineKeyboardButton(text='Deezer ☑️', callback_data=new_callback('page', 1)),
        InlineKeyboardButton(text='SoundCloud ✅', callback_data=new_callback('sc_page', 1)))
    return kb


def sc_artist_tracks_keyboard(tracks, artist_id):
    kb = InlineKeyboardMarkup(1)
    for i, track in enumerate(tracks[:97], start=1):
        kb.insert(InlineKeyboardButton(
            f'{i}. {track.title}',
            callback_data=new_callback('track_soundcloud', track.id, 'send')))
    kb.insert(InlineKeyboardButton('Get all tracks', callback_data=new_callback('sc_artist', artist_id, 'download')))
    kb.insert(InlineKeyboardButton('Go back', callback_data=new_callback('sc_artist', artist_id, 'main')))
    return kb


def sc_artist_playlists_keyboard(playlists, artist_id):
    kb = InlineKeyboardMarkup(1)
    for i, playlist in enumerate(playlists, start=1):
        kb.insert(InlineKeyboardButton(
            f'{i}. {playlist.title}',
            callback_data=new_callback('playlist_soundcloud', playlist.id, 'send')))
    kb.insert(InlineKeyboardButton('Go back', callback_data=new_callback('sc_artist', artist_id, 'main')))
    return kb


def sc_playlist_keyboard(playlist, post):
    kb = InlineKeyboardMarkup(1)
    for i, track in enumerate(playlist.tracks, start=1):
        kb.insert(InlineKeyboardButton(
            f'{i+1}. {track.artist} \u2013 {track.title}',
            callback_data=new_callback('track_soundcloud', playlist.id, 'send')))
    kb.insert(InlineKeyboardButton('Get all tracks', callback_data=new_callback('playlist_soundcloud', playlist.id, 'download')))
    if post:
        kb.insert(InlineKeyboardButton('Post', callback_data=new_callback('playlist_soundcloud', playlist.id, 'post')))
    return kb


def sc_artist_keyboard(artist):
    kb = InlineKeyboardMarkup(2)
    kb.insert(InlineKeyboardButton('Tracks', callback_data=new_callback('sc_artist', artist.id, 'tracks')))
    kb.insert(InlineKeyboardButton('Playlists', callback_data=new_callback('sc_artist', artist.id, 'playlists')))
    kb.insert(InlineKeyboardButton('Likes', callback_data=new_callback('sc_artist', artist.id, 'likes')))
    kb.insert(InlineKeyboardButton('Search on Last.Fm', url=str(URL(f'https://www.last.fm/search?q={artist.username}'))))
    return kb
