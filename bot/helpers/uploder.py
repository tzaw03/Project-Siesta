import os
import shutil
import asyncio
import bot.helpers.translations as lang
from config import Config
from .message import send_message, edit_message
from .utils import create_simple_text, rclone_upload, cleanup, format_string, post_simple_message, edit_art_poster

from ..settings import bot_set

async def track_upload(metadata, user, disable_link=False):
    if bot_set.upload_mode == 'Local':
        await local_upload(metadata, user)
    elif bot_set.upload_mode == 'Telegram':
        await telegram_upload(metadata, user)
    else:
        rclone_link, index_link = await rclone_upload(user, metadata['filepath'])
        if not disable_link:
            await post_simple_message(user, metadata, rclone_link, index_link)

    try:
        if os.path.exists(metadata['filepath']):
            os.remove(metadata['filepath'])
    except:
        pass

async def album_upload(metadata, user):
    if bot_set.upload_mode == 'Local':
        await local_upload(metadata, user)
    elif bot_set.upload_mode == 'Telegram':
        if bot_set.album_zip:
            for item in metadata['folderpath']:
                await send_message(user, item, 'doc', caption=await create_simple_text(metadata, user))
        else:
            await batch_telegram_upload(metadata, user)
    else:
        rclone_link, index_link = await rclone_upload(user, metadata['folderpath'])
        if metadata['poster_msg']:
            try:
                await edit_art_poster(metadata, user, rclone_link, index_link, await format_string(lang.s.ALBUM_TEMPLATE, metadata, user))
            except MessageNotModified:
                pass
        else:
            await post_simple_message(user, metadata, rclone_link, index_link)
    await cleanup(None, metadata)

# FIX: ImportError အတွက် artist_upload function ကို ဖြည့်စွက်ခြင်း
async def artist_upload(metadata, user):
    if bot_set.upload_mode == 'Local':
        await local_upload(metadata, user)
    elif bot_set.upload_mode == 'Telegram':
        if bot_set.artist_zip:
            for item in metadata['folderpath']:
                await send_message(user, item, 'doc', caption=await create_simple_text(metadata, user))
        else:
            await batch_telegram_upload(metadata, user)
    else:
        rclone_link, index_link = await rclone_upload(user, metadata['folderpath'])
        if metadata['poster_msg']:
            try:
                await edit_art_poster(metadata, user, rclone_link, index_link, await format_string(lang.s.ARTIST_TEMPLATE, metadata, user))
            except MessageNotModified:
                pass
        else:
            await post_simple_message(user, metadata, rclone_link, index_link)
    await cleanup(None, metadata)

async def playlist_upload(metadata, user):
    if bot_set.upload_mode == 'Local':
        await local_upload(metadata, user)
    elif bot_set.upload_mode == 'Telegram':
        if bot_set.playlist_zip:
            for item in metadata['folderpath']:
                await send_message(user, item, 'doc', caption=await create_simple_text(metadata, user))
        else:
            await batch_telegram_upload(metadata, user)
    else:
        rclone_link, index_link = await rclone_upload(user, metadata['folderpath'])
        if metadata['poster_msg']:
            try:
                await edit_art_poster(metadata, user, rclone_link, index_link, await format_string(lang.s.PLAYLIST_TEMPLATE, metadata, user))
            except MessageNotModified:
                pass
        else:
            await post_simple_message(user, metadata, rclone_link, index_link)
    await cleanup(None, metadata)

async def telegram_upload(track, user):
    """Only upload a single track"""
    await send_message(user, track['filepath'], 'audio', meta=track)

async def batch_telegram_upload(metadata, user):
    if metadata['type'] in ['album', 'playlist']:
        for track in metadata['tracks']:
            try:
                await telegram_upload(track, user)
            except:
                pass
    elif metadata['type'] == 'artist':
        for album in metadata['albums']:
            for track in album['tracks']:
                try:
                    await telegram_upload(track, user)
                except:
                    pass

async def local_upload(metadata, user):
    to_move = f"{Config.DOWNLOAD_BASE_DIR}/{user['r_id']}/{metadata['provider']}"
    destination = os.path.join(Config.LOCAL_STORAGE, os.path.basename(to_move))
    if os.path.exists(to_move):
        if os.path.exists(destination):
            for item in os.listdir(to_move):
                src_item = os.path.join(to_move, item)
                dest_item = os.path.join(destination, item)
                if os.path.isdir(src_item):
                    if not os.path.exists(dest_item): shutil.copytree(src_item, dest_item)
                else: shutil.copy2(src_item, dest_item)
        else:
            shutil.copytree(to_move, destination)
        shutil.rmtree(to_move)
