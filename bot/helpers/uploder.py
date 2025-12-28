import os
import shutil
from config import Config
from .message import send_message, edit_message
from .utils import *

async def track_upload(metadata, user, disable_link=False):
    if bot_set.upload_mode == 'Local':
        await local_upload(metadata, user)
    elif bot_set.upload_mode == 'Telegram':
        # send_message က Channel ထဲကိုပါ အလိုအလျောက် dump လုပ်သွားပါလိမ့်မယ်
        await telegram_upload(metadata, user)
    else:
        rclone_link, index_link = await rclone_upload(user, metadata['filepath'])
        if not disable_link:
            await post_simple_message(user, metadata, rclone_link, index_link)

    try:
        if os.path.exists(metadata['filepath']):
            os.remove(metadata['filepath'])
    except Exception as e:
        LOGGER.error(f"Cleanup Error: {e}")

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

# Artist နဲ့ Playlist upload တွေဟာလည်း telegram_upload/send_message ကိုပဲ သုံးတာမို့
# Channel Dump Feature က အလိုအလျောက် အလုပ်လုပ်ပါလိမ့်မယ်။

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
                await telegram_upload(track, user)

async def local_upload(metadata, user):
    to_move = f"{Config.DOWNLOAD_BASE_DIR}/{user['r_id']}/{metadata['provider']}"
    destination = os.path.join(Config.LOCAL_STORAGE, os.path.basename(to_move))
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

async def rclone_upload(user, realpath):
    path = f"{Config.DOWNLOAD_BASE_DIR}/{user['r_id']}/"
    cmd = f'rclone copy --config ./rclone.conf "{path}" "{Config.RCLONE_DEST}"'
    task = await asyncio.create_subprocess_shell(cmd)
    await task.wait()
    return await create_link(realpath, Config.DOWNLOAD_BASE_DIR + f"/{user['r_id']}/")
