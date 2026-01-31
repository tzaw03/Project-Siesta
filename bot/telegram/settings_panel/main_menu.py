from pyrogram import Client, filters
from pyrogram.types import CallbackQuery

from bot import CMD
from bot.helpers.translations import L
from bot.models.task import TaskDetails
from bot.buttons.settings import main_menu
from bot.utils.message import send_text, check_user, edit_message


@Client.on_message(filters.command(CMD.SETTINGS))
async def settings(c, message):
    if await check_user(message.from_user.id, restricted=True):
        task_details = TaskDetails(message, None)
        await send_text(L.INIT_SETTINGS_PANEL, task_details, markup=main_menu())


@Client.on_callback_query(filters.regex(pattern=r"^main_menu")) 
async def main_menu_cb(client, cb:CallbackQuery):
    if await check_user(cb.from_user.id, restricted=True):
        try:
            await edit_message(cb.message, L.INIT_SETTINGS_PANEL, markup=main_menu())
        except:
            pass

@Client.on_callback_query(filters.regex(pattern=r"^close"))
async def close_cb(client, cb:CallbackQuery):
    if await check_user(cb.from_user.id, restricted=True):
        try:
            await client.delete_messages(
                chat_id=cb.message.chat.id,
                message_ids=cb.message.id
            )
        except:
            pass