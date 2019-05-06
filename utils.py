import asyncio
import glob
import os
import random
import re
import string
from asyncio import sleep
from collections import namedtuple
from datetime import date
from functools import wraps
from time import time

import aiofiles
import mutagen
from aiogram import exceptions, types
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3
from eyed3 import id3
from yarl import URL

from var import var


def new_callback(*args, sep=':'):
    return sep.join(str(arg) for arg in args)


def parse_callback(callback, sep=':'):
    return callback.split(sep)


def random_string(length=10):
    return ''.join(random.sample(string.ascii_letters, length))


def clear_link(message):
    for entity in message.entities:
        if entity.type == 'url':
            return entity.url \
                or message.text[entity.offset : entity.offset + entity.length]


def split_string(text):
    result = []
    words = text.split('\n')
    string = ''
    for i, word in enumerate(words):
        if (len(string + word) > 4096):
            result.append(string)
            string = ''
        string += word + '\n'
        if i == len(words) - 1:
            result.append(string)
            string = ''
    return result


def already_downloading(track_id):
    status = var.downloading.get(track_id)  # pylint: disable=no-member
    if status is None or int(time()) - status > 60:
        return False
    return True


def islink(text):
    return 'https://' in text or 'http://' in text


Stats = namedtuple('Stats', ('downloaded_tracks',
                             'sent_tracks', 'received_messages'))


def get_today_stats():
    datestr = date.today().isoformat()
    downloaded_tracks = 0
    sent_tracks = 0
    received_messages = 0
    for filename in glob.iglob(f'logs/{datestr}*file_downloads.log'):
        downloaded_tracks += sum(1 for line in open(filename))
    for filename in glob.iglob(f'logs/{datestr}*sent_messages.log'):
        sent_tracks += sum(1 for line in open(filename))
    for filename in glob.iglob(f'logs/{datestr}*messages.log'):
        received_messages += sum(1 for line in open(filename))
    return Stats(downloaded_tracks, sent_tracks, received_messages)


def encode_url(url, *args, **kwargs):
    data = {}
    for arg in args:
        if isinstance(arg, dict):
            data.update(arg)
    data.update(kwargs)
    url = URL(url).with_query(data)
    return str(url)


def calling_queue(size):
    def wrapper(coro):
        sem = asyncio.Semaphore(size)
        @wraps(coro)
        async def decorator(*args, **kwargs):
            async with sem:
                result = await coro(*args, **kwargs)
            return result
        return decorator
    return wrapper


def retry(*exceptions, retries=3, cooldown=1):
    def wrap(func):
        @wraps(func)
        async def inner(*args, **kwargs):
            retries_count = 0

            while True:
                try:
                    result = await func(*args, **kwargs)
                except exceptions as err:
                    retries_count += 1
                    if retries_count > retries:
                        raise ValueError('Number of retries exceeded') from err
                    if cooldown:
                        await asyncio.sleep(cooldown)
                else:
                    return result
        return inner
    return wrap


@calling_queue(10)
async def download_file(url, path):
    r = await var.session.get(url)  # pylint: disable=no-member
    async with aiofiles.open(path, 'wb') as f:
        async for chunk in r.content.iter_chunked(2048):
            await f.write(chunk)


@calling_queue(10)
async def get_file(url, total_size=None):
    r = await var.session.get(url)  # pylint: disable=no-member
    return await r.content.read()


def add_tags(path, track, album, image, lyrics):
    try:
        genre = album['genres']['data'][0]['name']
    except (KeyError, IndexError):
        genre = ''

    tag = id3.Tag()
    tag.parse(path)
    tag.artist = track['artist']['name']
    tag.album = track['album']['title']
    tag.album_artist = album['artist']['name']
    tag.original_release_date = track['album']['release_date']
    tag.recording_date = int(track['album']['release_date'].split('-')[0])
    tag.title = track['title']
    tag.track_num = track['track_position']
    tag.disc_num = track['disk_number']
    tag.non_std_genre = genre
    tag.bpm = track['bpm']
    if lyrics:
        tag.lyrics.set(lyrics)
    tag.images.set(
        type_=3, img_data=image, mime_type='image/png')
    tag.save()


def sc_add_tags(path, track, image, lyrics=None):
    try:
        album_title = track['publisher_metadata']['album_title']
    except KeyError:
        album_title = ''

    tag = id3.Tag()
    tag.parse(path)
    tag.title = track.title
    tag.artist = track.artist
    tag.album = album_title
    tag.album_artist = track.artist if album_title else ''
    tag.original_release_date = track.created_at.split('T')[0].split(' ')[0].replace('/', '-')
    tag.non_std_genre = track.get('genre', '')
    if lyrics:
        tag.lyrics.set(lyrics)
    tag.images.set(
        type_=3, img_data=image, mime_type='image/png')
    tag.save()
