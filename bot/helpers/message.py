import os
import asyncio
from config import Config
from pyrogram.types import Message
from pyrogram.errors import MessageNotModified, FloodWait

from bot.tgclient import aio
from bot.settings import bot_set
from bot.logger import LOGGER

current_user = []

user_details = {
    'user_id': None,
    'name': None,
    'user_name': None,
    'r_id': None,
    'chat_id': None,
    'provider': None,
    'bot_msg': None,
    'link': None,
    'override' : None
}

async def fetch_user_details(msg: Message, reply=False) -> dict:
    details = user_details.copy()
    details['user_id'] = msg.from_user.id
    details['name'] = msg.from_user.first_name
    details['user_name'] = msg.from_user.username if msg.from_user.username else msg.from_user.mention()
    details['r_id'] = msg.reply_to_message.id if reply else msg.id
    details['chat_id'] = msg.chat.id
    details['bot_msg'] = msg.id
    return details

async def check_user(uid=None, msg=None, restricted=False) -> bool:
    if restricted:
        return uid in bot_set.admins
    if bot_set.bot_public:
        return True
    all_chats = list(bot_set.admins) + bot_set.auth_chats + bot_set.auth_users 
    return (msg.from_user.id in all_chats) or (msg.chat.id in all_chats)

async def antiSpam(uid=None, cid=None, revoke=False) -> bool:
    target = cid if bot_set.anti_spam == 'CHAT+' else uid
    if bot_set.anti_spam == 'OFF': return False
    if revoke:
        if target in current_user: current_user.remove(target)
    else:
        if target in current_user: return True
        current_user.append(target)
    return False

async def send_message(user, item, itype='text', caption=None, markup=None, chat_id=None, meta=None):
    if not isinstance(user, dict):
        user = await fetch_user_details(user)
    
    # Logic အဟောင်းအတိုင်း User ဆီ ပို့ခြင်း
    dest_id = chat_id if chat_id else user['chat_id']
    msg = await _perform_send(dest_id, user['r_id'], item, itype, caption, markup, meta)
    
    # MIGRATION: Channel Dump Logic
    # Channel ID ရှိခဲ့ရင် အဲဒီထဲကိုပါ တူညီတဲ့ file ကို ပို့ပေးမှာဖြစ်ပါတယ်
    if Config.DUMP_CHANNEL != 0 and itype in ['audio', 'doc', 'pic']:
        try:
            log_caption = f"📌 **From User:** {user['name']} (`{user['user_id']}`)\n🔗 **Link:** {user.get('link', 'N/A')}\n\n{caption if caption else ''}"
            await _perform_send(Config.DUMP_CHANNEL, None, item, itype, log_caption, None, meta)
        except Exception as e:
            LOGGER.error(f"DUMP ERROR: {e}")

    return msg

async def _perform_send(chat_id, reply_to, item, itype, caption, markup, meta):
    """Internal helper to handle pyrogram send methods"""
    try:
        if itype == 'text':
            return await aio.send_message(chat_id, item, reply_to_message_id=reply_to, reply_markup=markup, disable_web_page_preview=True)
        elif itype == 'doc':
            return await aio.send_document(chat_id, item, caption=caption, reply_to_message_id=reply_to)
        elif itype == 'audio':
            return await aio.send_audio(chat_id, item, caption=caption, duration=int(meta['duration']), 
                                      performer=meta['artist'], title=meta['title'], thumb=meta['thumbnail'], reply_to_message_id=reply_to)
        elif itype == 'pic':
            return await aio.send_photo(chat_id, item, caption=caption, reply_to_message_id=reply_to)
    except FloodWait as e:
        await asyncio.sleep(e.value)
        return await _perform_send(chat_id, reply_to, item, itype, caption, markup, meta)

async def edit_message(msg: Message, text, markup=None, antiflood=True):
    try:
        return await msg.edit_text(text, reply_markup=markup, disable_web_page_preview=True)
    except MessageNotModified:
        return None
    except FloodWait as e:
        if antiflood:
            await asyncio.sleep(e.value)
            return await edit_message(msg, text, markup, antiflood)
        return None
