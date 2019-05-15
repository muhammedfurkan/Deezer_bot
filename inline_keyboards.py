from math import ceil

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from yarl import URL
from utils import new_callback


finish_download_keyboard = InlineKeyboardMarkup(1)
finish_download_keyboard.insert(InlineKeyboardButton(
    'Loading full track, please wait...', callback_data='finish_download'))

start_keyboard = InlineKeyboardMarkup(1)
start_keyboard.insert(InlineKeyboardButton('Search', switch_inline_query_current_chat=''))
start_keyboard.insert(InlineKeyboardButton('Search albums', switch_inline_query_current_chat='.a '))
start_keyboard.insert(InlineKeyboardButton('Search artists', switch_inline_query_current_chat='.ar '))

large_file_keyboard = InlineKeyboardMarkup(1)
large_file_keyboard.insert(InlineKeyboardButton(
    "File is too big, Telegram won't let to upload it",
    callback_data='big_file'))

stats_keyboard = InlineKeyboardMarkup()
stats_keyboard.insert(InlineKeyboardButton('Update', callback_data='stats'))

today_stats_keyboard = InlineKeyboardMarkup()
today_stats_keyboard.insert(InlineKeyboardButton('Update', callback_data='today'))
