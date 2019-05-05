import re

from aiogram.dispatcher.filters import BoundFilter
from aiogram import types


# class SpotifyFilter(BoundFilter):
# 	key = 'spotify'

async def SpotifyFilter(self, message: types.Message):
	return 'open.spotify.com/track' in message.text


# class SpotifyPlaylistFilter(BoundFilter):
# 	key = 'spotify_playlist'

async def SpotifyPlaylistFilter(self, message: types.Message):
	return 'open.spotify.com/playlist' in message.text


# class SpotifyAlbumFilter(BoundFilter):
# 	key = 'spotify_album'

async def SpotifyAlbumFilter(self, message: types.Message):
	return 'open.spotify.com/album' in message.text


# class SpotifyArtistFilter(BoundFilter):
# 	key = 'spotify_artist'

async def SpotifyArtistFilter(self, message: types.Message):
	return 'open.spotify.com/artist' in message.text


# class DeezerFilter(BoundFilter):
# 	key = 'deezer'

async def DeezerFilter(self, message: types.Message):
	return re.match(r'.+deezer.com/??track/.+', message.text)


# class DeezerPlaylistFilter(BoundFilter):
# 	key = 'deezer_playlist'

async def DeezerPlaylistFilter(self, message: types.Message):
	return re.match(r'.+deezer.com/???playlist/.+', message.text)


# class DeezerAlbumFilter(BoundFilter):
# 	key = 'deezer_album'

async def DeezerAlbumFilter(self, message: types.Message):
	return re.match(r'.+deezer.com/???album/.+', message.text)


# class DeezerArtistFilter(BoundFilter):
# 	key = 'deezer_artist'

async def DeezerArtistFilter(self, message: types.Message):
	return re.match(r'.+deezer.com/???artist/.+', message.text)


# class ShazamFilter(BoundFilter):
# 	key = 'shazam'

async def ShazamFilter(self, message: types.Message):
	return 'shazam.com' in message.text


filters = (
	SpotifyFilter, SpotifyPlaylistFilter, SpotifyAlbumFilter,
	SpotifyArtistFilter, DeezerFilter, DeezerPlaylistFilter,
	DeezerAlbumFilter, DeezerArtistFilter, ShazamFilter)
