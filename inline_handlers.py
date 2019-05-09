from aiogram import types

import db_utils
import deezer_api
import inline_keyboards
import methods
import utils
from bot import bot
from var import var


async def inline_handler(query):
	q = query.query.replace('.a', '').replace('.ar', '').strip()
	results = []
	if not q:
		return await bot.answer_inline_query(
			inline_query_id=query.id,
			results=results,
			switch_pm_text='Search',
			switch_pm_parameter='0')
	if query.offset == 'done':
			return await bot.answer_inline_query(
				inline_query_id=query.id,
				results=results)

	if q:
		search_results = await deezer_api.search(q=q)

	if not search_results:
		return await bot.answer_inline_query(
		inline_query_id=query.id,
		results=results,
		switch_pm_text='Nothing was found',
		switch_pm_parameter='0')
		
	offset = int(query.offset) if query.offset.isdecimal() else 0

	if '.a' in query.query:
		already_in_list = []
		for result in search_results[offset : offset + 5]:
			if result.album.id in already_in_list:
				continue
			already_in_list.append(result.album.id)
			results.append(types.InlineQueryResultArticle(
				id=result.link,
				title=result.album.title,
				description=result.artist.name,
				thumb_url=result.album.cover_small,
				thumb_width=56,
				thumb_height=56,
				input_message_content=types.InputTextMessageContent(
					f'https://deezer.com/album/{result.album.id}')
				))
	else:
		for result in search_results[offset : offset + 5]:
			file_id = await db_utils.get_track(result.id)
			if file_id:
				results.append(types.InlineQueryResultCachedAudio(
					id='done:' + utils.random_string(), audio_file_id=file_id))
			elif result.preview:
				results.append(types.InlineQueryResultAudio(
					id=f'finish_download:{result.id}:{utils.random_string(4)}',
					audio_url=result.preview,
					title=f'⏳{result.title}',
					performer=result.artist.name,
					audio_duration=30,
					reply_markup=inline_keyboards.finish_download_keyboard)

	if offset + 6 < len(search_results):
			next_offset = str(offset + 5)
	else:
		next_offset = 'done'
	await bot.answer_inline_query(
		inline_query_id=query.id,
		results=results,
		next_offset=next_offset,
		cache_time=30)


async def artist_search_inline_handler(query):
	q = query.query.replace('.ar', '').strip()
	search_results = await deezer_api.search('artist', q)
	results = []
	if not q:
		return await bot.answer_inline_query(
			inline_query_id=query.id,
			results=results,
			switch_pm_text='Search',
			switch_pm_parameter='0')
	if query.offset == 'done':
			await bot.answer_inline_query(
				inline_query_id=query.id,
				results=results)
	offset = int(query.offset) if query.offset.isdecimal() else 0
	for result in search_results[offset : offset + 5]:
		results.append(types.InlineQueryResultArticle(
			id=result.link,
			title=result.name,
			thumb_url=result.picture_small,
			thumb_width=56,
			thumb_height=56,
			input_message_content=types.InputTextMessageContent(result.link)
			))

	if offset + 6 < len(search_results):
			next_offset = str(offset + 5)
	else:
		next_offset = 'done'
	await bot.answer_inline_query(
		inline_query_id=query.id,
		results=results,
		next_offset=next_offset)


async def finish_download_handler(chosen_inline: types.ChosenInlineResult):
	if utils.islink(chosen_inline.result_id):
		return
	if chosen_inline.result_id.split(':')[0] == 'done':
		return
	try:
		track_id = int(chosen_inline.result_id.split(':')[1])
	except ValueError:
		track_id = int(chosen_inline.result_id.split(':')[1].split('/')[-1])
	track = await deezer_api.gettrack(track_id)
	await methods.finish_download(track, chosen_inline.inline_message_id, chosen_inline.from_user)
