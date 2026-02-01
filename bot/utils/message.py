import asyncio
from typing import Optional

from pyrogram.errors import FloodWait, MessageNotModified
from pyrogram.types import Message

from bot import Config, LOGGER
from bot.settings import bot_settings
from bot.tgclient import siesta
from bot.helpers.translations import L
from bot.models.metadata import AlbumMetadata, PlaylistMetadata, ArtistMetadata


async def copy_to_channel(msg: Message) -> Message | None:
    """
    Copy a message to the configured copy channel.
    
    Args:
        msg: The Pyrogram Message object to copy.
    
    Returns:
        The copied message if successful, None otherwise.
    """
    if not Config.COPY_CHANNEL_ID or not msg:
        return None
    
    try:
        copied_msg = await safe_telegram_call(
            msg.copy,
            chat_id=Config.COPY_CHANNEL_ID
        )
        return copied_msg
    except Exception as e:
        LOGGER.error(f"Failed to copy message to channel {Config.COPY_CHANNEL_ID}: {e}")
        return None


current_user = set()


async def check_user(uid=None, msg=None, restricted: bool = False) -> bool:
    """
    Check whether a user or chat has access.

    Args:
        uid (int, optional): User ID (used when `restricted` is True).
        msg (pyrogram.types.Message, optional): Pyrogram message object, used to extract chat/user IDs.
        restricted (bool, optional): If True, restricts access to bot admins only.

    Returns:
        bool: True if access is allowed, False otherwise.
    """
    if restricted:
        return uid in bot_settings.admins

    if bot_settings.bot_public:
        return True

    all_allowed = set(bot_settings.admins) | set(bot_settings.auth_chats) | set(bot_settings.auth_users)
    if not msg:
        return False

    return msg.from_user.id in all_allowed or msg.chat.id in all_allowed


async def antiSpam(uid: int = None, cid: int = None, revoke: bool = False) -> bool:
    """
    Check or update anti-spam status for a user or chat.

    Args:
        uid (int, optional): User ID (used if anti-spam mode is 'USER').
        cid (int, optional): Chat ID (used if anti-spam mode is 'CHAT+').
        revoke (bool, optional): If True, removes the ID from anti-spam tracking.

    Returns:
        bool: True if currently in spam/waiting mode, False otherwise.
    """
    mode = bot_settings.anti_spam
    key = cid if mode == "CHAT+" else uid

    if key is None:
        return False

    global current_user

    if revoke:
        current_user.discard(key)
        return False

    if key in current_user:
        return True

    current_user.add(key)
    return False



async def safe_telegram_call(method, *args, retries=3, **kwargs) -> Message | None:
    """
    Safely call a Pyrogram client method with automatic FloodWait handling and retries.

    Args:
        method: The Pyrogram client method to call (e.g., client.send_message)
        *args: Positional arguments for the method
        retries (int): Number of retry attempts
        **kwargs: Keyword arguments for the method
    """
    for attempt in range(retries):
        try:
            return await method(*args, **kwargs)
        except FloodWait as e:
            wait_time = int(e.value)
            await asyncio.sleep(wait_time)
        except Exception as e:
            if attempt + 1 == retries:
                raise  # re-raise last error after final attempt
            await asyncio.sleep(2)


async def edit_message(msg:Message, text, markup=None, flood_wait=True):
    try:
        edited = await safe_telegram_call(
            msg.edit_text,
            text=text,
            reply_markup=markup,
            disable_web_page_preview=True
        )
        return edited
    except MessageNotModified:
        return None


async def send_document(document, task_details, chat_id: Optional[int] = None, caption=Optional[str]):
    if Config.DIRECT_TO_CHANNEL and Config.COPY_CHANNEL_ID:
        target_chat = Config.COPY_CHANNEL_ID
        reply_to = None
    else:
        target_chat = chat_id or task_details.chat_id
        reply_to = task_details.reply_to_message_id
    
    msg = await safe_telegram_call(
        siesta.send_document,
        chat_id=target_chat,
        document=document,
        caption=caption,
        reply_to_message_id=reply_to
    )
    
    if not Config.DIRECT_TO_CHANNEL:
        await copy_to_channel(msg)
    return msg


async def send_audio(audio, metadata, task_details, chat_id: Optional[int] = None, caption=Optional[str]):
    if Config.DIRECT_TO_CHANNEL and Config.COPY_CHANNEL_ID:
        target_chat = Config.COPY_CHANNEL_ID
        reply_to = None
    else:
        target_chat = chat_id or task_details.chat_id
        reply_to = task_details.reply_to_message_id
    
    msg = await safe_telegram_call(
        siesta.send_audio,
        chat_id=target_chat,
        reply_to_message_id=reply_to,
        caption=caption,
        duration=metadata.duration,
        performer=metadata.artist,
        title=metadata.title,
        thumb=metadata.thumbnail,
        audio=audio
    )
    
    if not Config.DIRECT_TO_CHANNEL:
        await copy_to_channel(msg)
    return msg


async def send_text(text, task_details, chat_id: Optional[int] = None, markup=None):
    chat_id = chat_id or task_details.chat_id
    msg = await safe_telegram_call(
        siesta.send_message,
        text=text,
        chat_id=chat_id,
        reply_to_message_id=task_details.reply_to_message_id,
        reply_markup=markup
    )
    return msg


async def send_art_post(metadata, task_details, chat_id: Optional[int] = None):
    """
    Send album/playlist/artist art with formatted caption.
    
    Args:
        metadata: AlbumMetadata, PlaylistMetadata, or ArtistMetadata object
        task_details: TaskDetails object containing chat info
        chat_id: Optional chat ID override
    
    Returns:
        The sent message if successful, None otherwise.
    """
    
    if Config.DIRECT_TO_CHANNEL and Config.COPY_CHANNEL_ID:
        target_chat = Config.COPY_CHANNEL_ID
        reply_to = None
    else:
        target_chat = chat_id or task_details.chat_id
        reply_to = task_details.reply_to_message_id
    
    cover = getattr(metadata, 'cover', None) or getattr(metadata, 'thumbnail', None)
    if not cover:
        return None
    
    if isinstance(metadata, AlbumMetadata):
        caption = L.ALBUM_TEMPLATE.format(
            title=metadata.title,
            artist=metadata.artist,
            date=metadata.date or 'N/A',
            totaltracks=metadata.totaltracks,
            totalvolume=metadata.totalvolume,
            quality=metadata.quality or 'N/A',
            provider=metadata.provider.title(),
            explicit='Yes' if metadata.explicit else 'No'
        )
    elif isinstance(metadata, PlaylistMetadata):
        caption = L.PLAYLIST_TEMPLATE.format(
            title=metadata.title,
            totaltracks=metadata.totaltracks,
            quality=getattr(metadata, 'quality', 'N/A') or 'N/A',
            provider=metadata.provider.title()
        )
    elif isinstance(metadata, ArtistMetadata):
        caption = L.ARTIST_TEMPLATE.format(
            artist=metadata.artist,
            quality=getattr(metadata, 'quality', 'N/A') or 'N/A',
            provider=metadata.provider.title()
        )
    else:
        return None
    
    try:
        msg = await safe_telegram_call(
            siesta.send_photo,
            chat_id=target_chat,
            photo=cover,
            caption=caption,
            reply_to_message_id=reply_to
        )
        if not Config.DIRECT_TO_CHANNEL:
            await copy_to_channel(msg)
        return msg
    except Exception as e:
        LOGGER.error(f"Failed to send art post: {e}")
        return None
        return None
