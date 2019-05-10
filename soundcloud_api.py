import asyncio
import re
from pprint import pprint
from sys import argv
import os

import aiofiles
import aiohttp
from asyncache import cached
from cachetools import TTLCache

from AttrDict import AttrDict
from config import soundcloud_client
from utils import download_file, get_file, sc_add_tags
import bot
from var import var

api = 'https://api.soundcloud.com'
api_v2 = 'https://api-v2.soundcloud.com'
split = re.compile(r'([^\-\–\—\⸺~]+) [\-–—⸺~] (.*)$')


@cached(TTLCache(100, 600))
async def api_call(obj, obj_id, method='', **params):
    req = await var.session.get(
        api + f'/{obj}/{obj_id}/{method}',
        params={'client_id': soundcloud_client, **params})
    return await req.json()


class SoundCloudTrack(AttrDict):
    def __init__(self, mapping):
        super().__init__(mapping)
        try:
            self.artist, self.title = re.findall(split, mapping['title'])[0]
        except IndexError:
            self.artist, self.title = mapping['user']['username'], mapping['title']

    async def download_url(self):
        r = await var.session.get(
            api + f'/tracks/{self.id}/stream',
            params={'client_id': soundcloud_client})
        return r.url

    async def download(self, filepath=None):
        if not filepath:
            os.makedirs(f'downloads/{self.id}', exist_ok=True)
            filepath = \
                f'downloads/{self.id}/ ' + \
                f'{self.user.username} - {self.title}'.replace('/', '_')[:97] + '.mp3'
        else:
            os.makedirs(filepath.rsplit('/', 1)[0], exist_ok=True)

        print(f'[Soundcloud]Start downloading: {self.id} | {self.artist} - {self.title}')
        await download_file(await self.download_url(), filepath)
        cover = await get_file(self.artwork_url)
        sc_add_tags(filepath, self, cover)
        print(f'[Soundcloud]Finished downloading: {self.id} | {self.artist} - {self.title}')
        return filepath

    @property
    def artwork_url(self):
        return self['artwork_url'].replace('large', 't500x500')

    @property
    def duration(self):
        return int(self['duration'] / 1000)


class SoundCloudArtist(AttrDict):
    def __init__(self, mapping):
        super().__init__(mapping)

    @property
    def avatar_url(self):
        return self['avatar_url'].replace('large', 't500x500')

    async def get_tracks(self, limit=200):
        res = api_call('user', self.id, 'tracks', limit=limit)
        return [SoundCloudTrack(track) for track in res]

    async def get_likes(self, limit=200):
        res = api_call('user', self.id, 'likes', limit=limit)
        return [SoundCloudTrack(track) for track in res]

    async def get_reposts(self, limit=200):
        res = api_call('user', self.id, 'reposts', limit=limit)
        return [SoundCloudTrack(track) for track in res]

    async def get_playlists(self, limit=200):
        res = api_call('user', self.id, 'playlists', limit=limit)
        return [SoundCloudPlaylist(playist) for playist in res]

    async def get_albums(self, limit=200):
        res = api_call('user', self.id, 'albums', limit=limit)
        return [SoundCloudPlaylist(album) for album in res]


class SoundCloudPlaylist(AttrDict):
    def __init__(self, mapping):
        super().__init__(mapping)

    @property
    def tracks(self):
        return [SoundCloudTrack(track) for track in self['tracks']]

    @property
    def artwork_url(self):
        return self['artwork_url'].replace('large', 't500x500')
        

async def resolve(url):
    req = await var.session.get(
        api + '/resolve', params={'url': url, 'client_id': soundcloud_client})
    res = await req.json()
    if res['kind'] == 'user':
        return SoundCloudArtist(res)        
    elif res['kind'] == 'track':
        return SoundCloudTrack(res)


@cached(TTLCache(100, 600))
async def search(q, limit=200, **params):
    req = await var.session.get(
        api_v2 + '/search/tracks',
        params={
            'q': q, 'client_id': soundcloud_client,
            'limit': limit, **params})
    result = (await req.json())['collection']
    return [SoundCloudTrack(track) for track in result]


@cached(TTLCache(100, 600))
async def get_track(track_id):
    req = await var.session.get(
        api + f'/tracks/{track_id}',
        params={'client_id': soundcloud_client})
    result = await req.json()
    return SoundCloudTrack(result)


@cached(TTLCache(100, 600))
async def get_artist(artist_id):
    req = await var.session.get(
        api + f'/users/{artist_id}',
        params={'client_id': soundcloud_client})
    result = await req.json()
    return SoundCloudArtist(result)




async def main():
    # track = await get_track(347808757)
    # print(track['title'])

    # query = ' '.join(argv[1:])
    query = 'jaron'
    for res in await search(query, kind='user'):
        pprint(res)
        # print(await res.download())


if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())
