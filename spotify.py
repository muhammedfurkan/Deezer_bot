import requests
import base64
import re
from time import time

from AttrDict import AttrDict
from utils import encode_url
from var import var

spotify_track = re.compile(r'open.spotify.com/track/[^? ]+')
spotify_album = re.compile(r'open.spotify.com/album/[^? ]+')
spotify_artist = re.compile(r'open.spotify.com/artist/[^? ]+')
spotify_playlist = re.compile(r'open.spotify.com/.+/playlist/[^? ]+')

class Spotify_API:
	def __init__(self, client, secret):
		self.client = client
		self.secret = secret
		s = self.client + ':' + self.secret
		self.auth = base64.urlsafe_b64encode(s.encode()).decode()
		r = requests.post(
			'https://accounts.spotify.com/api/token',
			headers={
				'Authorization': f'Basic {self.auth}',
				'Content-Type': 'application/x-www-form-urlencoded'},
			data={'grant_type': 'client_credentials'})
		json = r.json()
		self.token_type = json['token_type']
		self.token = json['access_token']
		self.expires_in = time() + json['expires_in']

	async def restart(self):
		self.__init__(self.client, self.secret)

	async def search(self, query, obj_type='track', limit=5):
		if self.expires_in < time():
			self.restart()
		data = {'type': obj_type, 'limit': limit, 'q': query}
		headers = {'Authorization': f'Bearer {self.token}'}
		r = await var.session.get(encode_url(
			'https://api.spotify.com/v1/search', data=data), headers=headers)
		json = await r.json(content_type=None)
		result = []
		if json['tracks']['total'] != 0:
			for item in json['tracks']['items']:
				result.append(AttrDict(item))
		return result

	async def get_track(self, url, retries=0):
		if self.expires_in < time():
			self.restart()
		if retries > 3:
			raise ValueError('Cannot get track')
		url = re.findall(spotify_track, url)[0]
		url = 'https://' + url
		track_id = url.split('/')[-1]
		r = await var.session.get(
			f'https://api.spotify.com/v1/tracks/{track_id}',
			headers={'Authorization': f'Bearer {self.token}'})
		print(r.url)
		json = await r.json()
		try:
			json['error']
		except KeyError:
			return AttrDict(json)
		else:
			self.restart()
			return await self.get_track(url, retries + 1)

	async def get_playlist(self, url):
		if self.expires_in < time():
			self.restart()
		url = re.findall(spotify_playlist, url)[0]
		playlist_id = url.split('/')[-1]
		r = await var.session.get(
			f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks',
			headers={'Authorization': f'Bearer {self.token}'})
		print(r.url)
		json = await r.json()
		if not json.get('error'):
			return [AttrDict(track['track']) for track in json['items']]
		else:
			raise ValueError('Error getting playlist: ' + json.get('error'))

	async def get_album(self, url):
		if self.expires_in < time():
			self.restart()
		url = re.findall(spotify_album, url)[0]
		album_id = url.split('/')[-1]
		r = await var.session.get(
			f'https://api.spotify.com/v1/albums/{album_id}',
			headers={'Authorization': f'Bearer {self.token}'})
		print(r.url)
		json = await r.json()
		if not json.get('error'):
			return AttrDict(json)
		else:
			raise ValueError('Error getting albums: ' + json.get('error'))

		
	async def get_artist(self, url):
		if self.expires_in < time():
			self.restart()
		url = re.findall(spotify_artist, url)[0]
		artist_id = url.split('/')[-1]
		r = await var.session.get(
			f'https://api.spotify.com/v1/artists/{artist_id}',
			json={'Authorization': f'Bearer {self.token}'})
		print(r.url)
		json = await r.json()
		if not json.get('error'):
			return AttrDict(json)
		else:
			raise ValueError('Error getting artist: ' + json.get('error'))


if __name__ == '__main__':
	pass
