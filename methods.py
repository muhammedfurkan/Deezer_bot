import asyncio
import json
import os
import shutil
from asyncio import sleep
from time import time

from aiogram import exceptions, types

import db_utils
import deezer_api
import soundcloud_api
import inline_keyboards
import config
from bot import bot
from logger import file_download_logger, format_name, sent_message_logger
from utils import already_downloading, calling_queue
from var import var
from userbot import post_large_track


@calling_queue(3)
async def upload_track(track, path, tries=0):
	if tries > 3:
		raise RuntimeError('can\'t upload track')
	try:
		msg = await bot.send_audio(
			chat_id=-1001246220493,
			audio=types.InputFile(path),
			title=track.title,
			performer=track.artist.name,
			duration=track.duration)
	except exceptions.RetryAfter as e:
		print(f'flood control exceeded, sleeping for {e.timeout + 10} seconds')
		await sleep(e.timeout + 10)
		return await upload_track(track, path, tries + 1)
	except exceptions.TelegramAPIError:
		await sleep(5)
		return await upload_track(track, path, tries + 1)
	return msg


async def finish_download(track, inline_message_id, user):
	file_id = await db_utils.get_track(track.id)
	if file_id:
		return await bot.edit_message_media(
			media = types.InputMediaAudio(
				media=file_id,
				title=track.title,
				performer=track.artist.name,
				duration=track.duration),
		inline_message_id=inline_message_id)
	path = await track.download()
	if (os.path.getsize(path) >> 20) > 50:
		await bot.edit_message_reply_markup(
			inline_message_id=inline_message_id,
			reply_markup=inline_keyboards.large_file_keyboard())
		await post_large_track(path, track)
		file_id = await db_utils.get_track(track.id)
	else:
		msg = await upload_track(track, path)
		await db_utils.add_track(track.id, msg.audio.file_id)
		file_id = msg.audio.file_id

	try:
		await bot.edit_message_media(
			media = types.InputMediaAudio(
				media=file_id,
				title=track.title,
				performer=track.artist.name,
				duration=track.duration),
			inline_message_id=inline_message_id)
		shutil.rmtree(path.rsplit('/', 1)[0])
	except exceptions.BadRequest:
		try:
			await bot.send_audio(user.id, file_id)
		except:
			pass
	
	file_download_logger.info(
		f'[downloaded track {track.id} (inline)] {track}')
	sent_message_logger.info(
		f'[send track {track.id} to {format_name(user)} (inline)] {track}')


async def send_track(track, chat, Redownload=False):
	quality = await db_utils.get_quality_setting(chat.id)
	if not already_downloading(track.id):
		var.downloading[track.id] = int(time())
	else:
		return
	if not Redownload:
		if (await check_and_forward(track, chat, quality)):
			return

	if quality == 'mp3':
		path = await track.download('MP3_320')
	elif quality == 'flac':
		path = await track.download('FLAC')		

	await bot.send_chat_action(chat.id, 'upload_audio')

	if (os.path.getsize(path) >> 20) > 50:
		msg = await bot.send_message(
			chat_id=chat.id,
			text='File is larger than 50 MB, uploading can take a while, please wait') 
		await post_large_track(path, track, quality)
		await sleep(1)
		file_id = await db_utils.get_track(track.id, quality)
		await bot.send_audio(chat.id, file_id)
		await msg.delete()
	else:
		msg = await upload_track(track, path)
		await msg.forward(chat.id)
		await db_utils.add_track(track.id, msg.audio.file_id, quality)
	shutil.rmtree(path.rsplit('/', 1)[0])
	var.downloading.pop(track.id)
	sent_message_logger.info(
		f'[send track {track.id} to {format_name(chat)}] {track}')


async def send_album(album, chat, pic=True, send_all=False):
	if pic:
		if not send_all:
			tracks = await album.get_tracks()
			markup = inline_keyboards.album_keyboard(
				album, tracks, chat.id in config.admins)
		else:
			markup = None
		await bot.send_photo(
			chat.id,
			album.cover_xl,
			caption=f'{album["artist"]["name"]} \u2013 {album.title}',
			reply_markup=markup)
	if send_all:
		for track in await album.get_tracks():
			print(track.title)
			await send_track(track, chat)


async def send_artist(artist, chat_id):
	await bot.send_photo(
		chat_id=chat_id,
		photo=artist.picture_xl,
		caption=f'[{artist.name}]({artist.share})',
		parse_mode='markdown',
		reply_markup=inline_keyboards.artist_keyboard(artist))


async def check_and_forward(track, chat, quality='mp3'):
	file_id = await db_utils.get_track(track.id, quality)
	if not file_id:
		return False
	await bot.send_audio(
		chat_id=chat.id, audio=file_id, title=track.title,
		performer=track.artist.name, duration=track.duration)
	sent_message_logger.info(
		f'[send track {track.id} to {format_name(chat)}] {track}')
	return True


async def cache(track):
	file_id = await db_utils.get_track(track.id)
	if not file_id:
		path = await track.download()
		if (os.path.getsize(path) >> 20) > 50:
			await post_large_track(path, track)
		else:
			msg = await upload_track(track, path)
			await db_utils.add_track(track.id, msg.audio.file_id)
		shutil.rmtree(path.rsplit('/', 1)[0])
		print(f'cached track {track.artist.name} - {track.title}')
	else:
		print(f'skipping track {track.artist.name} - {track.title} - {file_id}')


async def send_sc_track(track_id, chat_id):
	track = await soundcloud_api.get_track(track_id)
	path = await track.download()
	with open(path, 'rb') as f:
		await bot.send_audio(
			chat_id=chat_id, audio=f,
			performer=track.artist, title=track.title)
	os.remove(path)


async def send_soundcloud_track(chat_id, track):
	file_id = await db_utils.get_sc_track(track.id)
	if file_id:
		return await bot.send_audio(chat_id, file_id)
	path = await track.download()
	await bot.send_chat_action(chat_id, 'upload_audio')
	msg = await bot.send_audio(
		chat_id=chat_id,
		audio=types.InputFile(path),
		performer=track.artist,
		title=track.title)
	await db_utils.add_sc_track(track.id, msg.audio.file_id)
	shutil.rmtree(path.rsplit('/', 1)[0])
