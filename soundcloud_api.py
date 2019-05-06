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
            filepath = f'downloads/{self.id}/{self.user.username} - {self.title}.mp3'
        else:
            os.makedirs(filepath.rsplit('/', 1)[0], exist_ok=True)

        await download_file(await self.download_url(), filepath)
        cover = await get_file(self.artwork_url)
        sc_add_tags(filepath, self, cover)
        return filepath

    @property
    def artwork_url(self):
        return self['artwork_url'].replace('large', 't500x500')

    @property
    def duration(self):
        return int(self['duration'] / 1000)


@cached(TTLCache(100, 600))
async def search(q, **params):
    req = await var.session.get(
        api_v2 + '/search/tracks',
        params={'q': q, 'client_id': soundcloud_client, **params})
    result = (await req.json())['collection']
    return [SoundCloudTrack(track) for track in result]


@cached(TTLCache(100, 600))
async def get_track(track_id=None, url=None):
    if track_id:
        req = await var.session.get(
            api + f'/tracks/{track_id}',
            params={'client_id': soundcloud_client})
    elif url:
        req = await var.session.get(
            api + f'/resolve',
            params={'url': url, 'client_id': soundcloud_client})
    result = await req.json()
    return SoundCloudTrack(result)


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
