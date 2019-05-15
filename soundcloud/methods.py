import shutil
import os


from aiogram import types, exceptions

import db_utils
import utils
from bot import bot
from userbot import post_large_track
from . import keyboards

async def send_soundcloud_track(chat_id, track):
	file_id = await db_utils.get_sc_track(track.id)
	if file_id:
		return await bot.send_audio(chat_id, file_id)
	path = await track.download()
	if (os.path.getsize(path) >> 20) > 50:
		await post_large_track(path, track, provider='soundcloud')
		file_id = await db_utils.get_sc_track(track.id)
		return await bot.send_audio(chat_id, file_id)

	await bot.send_chat_action(chat_id, 'upload_audio')
	# thumb = await get_file(track.thumb_url)
	msg = await bot.send_audio(
		chat_id=chat_id,
		audio=types.InputFile(path),
		performer=track.artist,
		title=track.title,
		# thumb=types.InputFile(thumb)
		)
	await db_utils.add_sc_track(track.id, msg.audio.file_id)
	shutil.rmtree(path.rsplit('/', 1)[0])


async def send_soundcloud_artist(chat_id, artist):
	await bot.send_photo(
		chat_id=chat_id,
		photo=artist.avatar_url,
		caption=f'[{artist.username}]({artist.permalink_url})',
		parse_mode='markdown',
		reply_markup=keyboards.sc_artist_keyboard(artist))


async def send_soundcloud_playlist(chat_id, playlist, pic=True, send_all=False):
	if pic:
		if not send_all:
			markup = keyboards.sc_playlist_keyboard(
				playlist, chat_id in config.admins)
		else:
			markup = None
		try:
			await bot.send_photo(
				chat_id, playlist.artwork_url, reply_markup=markup,
				caption=f'{playlist.user.username} \u2013 {playlist.title}')
		except exceptions.BadRequest:
			await bot.send_photo(
				chat_id, playlist.tracks[0].artwork_url, reply_markup=markup,
				caption=f'{playlist.user.username} \u2013 {playlist.title}')
	if send_all:
		for track in playlist.tracks:
			print(track.title)
			await send_soundcloud_track(chat_id, track)
