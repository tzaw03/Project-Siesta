from bot.helpers.translations import L, LANGS

from bot.settings import bot_settings
from pyrogram.types import InlineKeyboardButton as Button, InlineKeyboardMarkup

main_button = [[Button(text=L.MAIN_MENU_BUTTON, callback_data="main_menu")]]
close_button = [[Button(text=L.CLOSE_BUTTON, callback_data="close")]]


def main_menu():
    inline_keyboard = [
        [Button(text=L.CORE,callback_data='corePanel')],
        [Button(text=L.TELEGRAM,callback_data='tgPanel')],
        [Button(text=L.PROVIDERS,callback_data='providerPanel')]
    ]
    inline_keyboard += close_button
    return InlineKeyboardMarkup(inline_keyboard)


def providers_button():
    inline_keyboard = []
    if bot_settings.qobuz:
        inline_keyboard.append([Button(text=L.QOBUZ, callback_data='qbP')])
    if bot_settings.deezer:
        inline_keyboard.append([Button(text=L.DEEZER, callback_data='dzP')])
    if bot_settings.can_enable_tidal:
        inline_keyboard.append([Button(text=L.TIDAL, callback_data='tdP')])
    inline_keyboard += main_button + close_button
    return InlineKeyboardMarkup(inline_keyboard)


def tg_button():
    inline_keyboard = [
        [Button(text=L.BOT_PUBLIC.format(bot_settings.bot_public), callback_data='botPublic')],
        [Button(text=L.ANTI_SPAM.format(bot_settings.anti_spam), callback_data='antiSpam')],
        [Button(text=L.LANGUAGE, callback_data='langPanel')]
    ]
    inline_keyboard += main_button + close_button
    return InlineKeyboardMarkup(inline_keyboard)


def core_buttons():
    inline_keyboard = []

    if bot_settings.rclone:
        inline_keyboard.append([Button(text=f"Return Link : {bot_settings.link_options}", callback_data='linkOptions')])

    inline_keyboard += [
        [Button(text=f"Upload : {bot_settings.upload_mode.value}", callback_data='upload')],
        [
            Button(text=L.SORT_PLAYLIST.format(bot_settings.playlist_sort), callback_data='sortPlay'),
            Button(text=L.DISABLE_SORT_LINK.format(bot_settings.disable_sort_link), callback_data='sortLinkPlay')],
        [
            Button(text=L.PLAYLIST_ZIP.format(bot_settings.playlist_zip), callback_data='playZip'),
            Button(text=L.PLAYLIST_CONC_BUT.format(bot_settings.playlist_conc), callback_data='playCONC')
        ],
        [
            Button(text=L.ARTIST_BATCH_BUT.format(bot_settings.artist_batch), callback_data='artBATCH'),
            Button(text=L.ARTIST_ZIP.format(bot_settings.artist_zip), callback_data='artZip')
        ],
        [
            Button(text=L.ALBUM_ZIP.format(bot_settings.album_zip), callback_data='albZip'),
            Button(text=L.POST_ART_BUT.format(bot_settings.art_poster), callback_data='albArt')
        ]
    ]
    inline_keyboard += main_button + close_button
    return InlineKeyboardMarkup(inline_keyboard)



def language_buttons():
    inline_keyboard = []
    selected = bot_settings.bot_lang
    for name, item in LANGS.values():
        text = f"{item.__language__} ✅" if item.__language__ == selected else item.__language__
        inline_keyboard.append(
            [Button(text=text.upper(), callback_data=f'langSet_{item.__language__}')]
        )
    inline_keyboard += main_button+ close_button
    return InlineKeyboardMarkup(inline_keyboard)