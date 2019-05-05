import datetime
import logging
import os
from asyncio import CancelledError, sleep

# logging.basicConfig(format='[%(asctime)s] %(message)s', datefmt='%m/%d/%Y %H:%M:%S')
message_logger = logging.getLogger('messages')
message_logger.setLevel('INFO')
sent_message_logger = logging.getLogger('sent_messages')
sent_message_logger.setLevel('INFO')
file_download_logger = logging.getLogger('file_downloads')
file_download_logger.setLevel('INFO')
error_logger = logging.getLogger('errors')
error_logger.setLevel('INFO')

async def update_logging_files():
    global message_logger, sent_message_logger, file_download_logger, error_logger
    print('start logging')
    while True:
        try:
            message_logger = logging.getLogger('messages')
            message_handler = logging.FileHandler(
                get_logger_filename('messages'), mode='a')
            message_logger.addHandler(message_handler)

            sent_message_logger = logging.getLogger('sent_messages')
            sent_message_handler = logging.FileHandler(
                get_logger_filename('sent_messages'), mode='a')
            sent_message_logger.addHandler(sent_message_handler)

            file_download_logger = logging.getLogger('file_downloads')
            file_download_handler = logging.FileHandler(
                get_logger_filename('file_downloads'), mode='a')
            file_download_logger.addHandler(file_download_handler)
        
            error_logger = logging.getLogger('errors')
            error_handler = logging.FileHandler(
                get_logger_filename('errors'), mode='a')
            error_logger.addHandler(error_handler)

            await sleep(300)

            message_logger.removeHandler(message_handler)
            sent_message_logger.removeHandler(sent_message_handler)
            file_download_logger.removeHandler(file_download_handler)
            error_logger.removeHandler(error_handler)

        except CancelledError:
            print('stopped logging')
            return


def get_logger_filename(filename):
    datestr = datetime.date.today().isoformat()
    hour = datetime.datetime.now().hour
    os.makedirs(f'logs/{datestr}/', exist_ok=True)
    filename = f'logs/{datestr}/{hour}_{filename}.log'
    return filename

def log_sent_track(chat, track, time):
    sent_message_logger.info(
        f'[track sent to {format_name(chat)}] {track.artist.name} - {track.title} - {track.album.title}')


def log_file_download(track):
    file_download_logger.info(
        f'[]')


def format_name(user):
	if not user.username:
		return user.full_name
	return user.full_name + ' - ' + user.username
