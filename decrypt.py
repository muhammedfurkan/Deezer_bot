import os
from hashlib import md5
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

import aiofiles
from aiostream.stream import enumerate as asyncenumerate

from var import var
from utils import calling_queue, request_get


def get_blowfish_key(SNG_ID):
        SECRET = b'g4el58wc0zvf9na1'

        id_md5 = bytes(md5(SNG_ID).hexdigest(), 'ascii')
        bf_key = b''
        for i in range(16):
            bf_key += bytes(chr(id_md5[i] ^ id_md5[i + 16] ^ SECRET[i]), 'ascii')

        return bf_key


@calling_queue(10)
async def dl_and_decrypt_track(url, SNG_ID, filename):
    SNG_ID = str(SNG_ID).encode('ascii')
    blowfish_key = get_blowfish_key(SNG_ID)
    async with aiofiles.open(filename, 'wb') as filestream:
        r = await request_get(url) # pylint: disable=no-member
        async for i, chunk in asyncenumerate(r.content.iter_chunked(2048)):
            if i % 3 or len(chunk) < 2048:
                await filestream.write(chunk)
            else:
                cipher = Cipher(algorithms.Blowfish(blowfish_key),
                                modes.CBC(bytes([i for i in range(8)])),
                                default_backend())
                decryptor = cipher.decryptor()
                chunk = decryptor.update(chunk) + decryptor.finalize()
                await filestream.write(chunk)


async def decrypt_track(track_buffer, info, out_filename):
    SNG_ID = str(info['SNG_ID']).encode('ascii')
    blowfish_key = get_blowfish_key(SNG_ID)
    async with aiofiles.open(out_filename, 'wb') as decrypted_stream:
        chunk_size = 2048
        progress = 0
        file_length = len(track_buffer)

        while progress < file_length:
            if (file_length - progress) < 2048:
                chunk_size = file_length - progress

            chunk = track_buffer[progress : progress + chunk_size]
            if progress % (chunk_size * 3) == 0 and chunk_size == 2048:
                cipher = Cipher(algorithms.Blowfish(blowfish_key),
                                modes.CBC(bytes([i for i in range(8)])),
                                default_backend())
                decryptor = cipher.decryptor()
                chunk = decryptor.update(chunk) + decryptor.finalize()

            await decrypted_stream.write(chunk)
            progress += chunk_size


def get_dl_url(privateInfo, quality):
    char = b'\xa4'.decode('unicode_escape')
    step1 = char.join((privateInfo['MD5_ORIGIN'],
                      str(quality), privateInfo['SNG_ID'],
                      privateInfo['MEDIA_VERSION']))
    m = md5()
    m.update(bytes([ord(x) for x in step1]))
    step2 = m.hexdigest() + char + step1 + char
    step2 = step2.ljust(80, ' ')
    cipher = Cipher(algorithms.AES(bytes('jo6aey6haid2Teih', 'ascii')),
                    modes.ECB(), default_backend())
    encryptor = cipher.encryptor()
    step3 = encryptor.update(bytes([ord(x) for x in step2])).hex()
    cdn = privateInfo['MD5_ORIGIN'][0]
    decryptedUrl = f'https://e-cdns-proxy-{cdn}.dzcdn.net/mobile/1/{step3}'
    return decryptedUrl
