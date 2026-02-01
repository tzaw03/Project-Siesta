from pyrogram import Client, filters
from pyrogram.types import CallbackQuery

from bot import Config
from bot.settings import bot_settings

from bot.buttons.settings import providers_button
from bot.buttons.tidal import *
from bot.buttons.qobuz import *

from bot.models.types import QobuzQuality, TidalQuality, TidalSpatial
from bot.helpers.database.pg_impl import settings_db

from bot.providers.tidal.tidal_api import tidalapi
from bot.providers.qobuz.qopy import qobuz_api


from bot.utils.message import edit_message, check_user
from bot.helpers.translations import L



@Client.on_callback_query(filters.regex(pattern=r"^providerPanel"))
async def provider_cb(c, cb:CallbackQuery):
    if await check_user(cb.from_user.id, restricted=True):
        await edit_message(
            cb.message,
            L.PROVIDERS_PANEL,
            providers_button()
        )


#----------------
# QOBUZ
#----------------
@Client.on_callback_query(filters.regex(pattern=r"^qbP"))
async def qobuz_cb(c, cb: CallbackQuery):
    if await check_user(cb.from_user.id, restricted=True):
        current_id = qobuz_api.quality

        quality_display = {}
        for q in QobuzQuality:
            text = q.name
            if q.value == current_id: text += ' ✅'
            quality_display[text] = q.value

        try:
            await edit_message(
                cb.message,
                L.QOBUZ_QUALITY_PANEL,
                markup=qb_button(quality_display)
            )
        except Exception:
            pass

@Client.on_callback_query(filters.regex(pattern=r"^qbQ"))
async def qobuz_quality_cb(c, cb: CallbackQuery):
    if await check_user(cb.from_user.id, restricted=True):
        try:
            data_id = int(cb.data.split('_')[1])
            new_quality = QobuzQuality(data_id)

            qobuz_api.quality = new_quality.value
            settings_db.set_variable('QOBUZ_QUALITY', new_quality.value)

            await qobuz_cb(c, cb)
        except (ValueError, IndexError):
            pass


#----------------
# TIDAL
#----------------
@Client.on_callback_query(filters.regex(pattern=r"^tdP"))
async def tidal_cb(c, cb:CallbackQuery):
    if await check_user(cb.from_user.id, restricted=True):
        await edit_message(
            cb.message,
            L.TIDAL_PANEL,
            tidal_buttons() # auth and quality button (quality button only if auth already done)
        )
    

@Client.on_callback_query(filters.regex(pattern=r"^tdQ"))
async def tidal_quality_cb(c, cb: CallbackQuery):
    if await check_user(cb.from_user.id, restricted=True):
        quality_display = {}
        for q in TidalQuality:
            if q == TidalQuality.MAX and not tidalapi.mobile_hires:
                continue
            text = q.value
            if tidalapi.quality == q.name: text += ' ✅'
            quality_display[q.name] = text

        try:
            await edit_message(
                cb.message,
                L.TIDAL_PANEL,
                markup=tidal_quality_button(quality_display)
            )
        except Exception:
            pass



@Client.on_callback_query(filters.regex(pattern=r"^tdSQ"))
async def tidal_set_quality_cb(c, cb: CallbackQuery):
    if await check_user(cb.from_user.id, restricted=True):
        action_key = cb.data.split('_')[1]

        if action_key == 'spatial':
            allowed_spatial = [TidalSpatial.OFF, TidalSpatial.ATMOS_AC3]
            if tidalapi.mobile_atmos:
                allowed_spatial.append(TidalSpatial.ATMOS_AC4)
            if tidalapi.mobile_atmos or tidalapi.mobile_hires:
                allowed_spatial.append(TidalSpatial.SONY_360RA)

            try:
                current_enum = next(s for s in allowed_spatial if s.value == tidalapi.spatial)
                current_idx = allowed_spatial.index(current_enum)
            except (StopIteration, ValueError):
                current_idx = 0

            next_idx = (current_idx + 1) % len(allowed_spatial)
            new_setting = allowed_spatial[next_idx]
            tidalapi.spatial = new_setting.value
            settings_db.set_variable('TIDAL_SPATIAL', new_setting.value)

        else:
            if action_key in TidalQuality.__members__:
                new_quality = TidalQuality[action_key]
                tidalapi.quality = new_quality.value
                settings_db.set_variable('TIDAL_QUALITY', tidalapi.quality)

        await tidal_quality_cb(c, cb)


# show login button if not logged in
# show refresh button in case logged in exist (both tv and mobile)
@Client.on_callback_query(filters.regex(pattern=r"^tdAuth"))
async def tidal_auth_cb(c, cb:CallbackQuery):
    if await check_user(cb.from_user.id, restricted=True):
        sub = tidalapi.sub_type
        hires = True if tidalapi.mobile_hires else False
        atmos = True if tidalapi.mobile_atmos else False
        tv = True if tidalapi.tv_session else False

        await edit_message(
            cb.message,
            L.TIDAL_AUTH_PANEL.format(sub, hires, atmos, tv),
            tidal_auth_buttons()
        )


@Client.on_callback_query(filters.regex(pattern=r"^tdLogin"))
async def tidal_login_cb(c:Client, cb:CallbackQuery):
    if await check_user(cb.from_user.id, restricted=True):
        auth_url = await tidalapi.get_tv_login_url(
            Config.TIDAL_TV_TOKEN,
            Config.TIDAL_TV_SECRET,
            Config.TIDAL_MOBILE_TOKEN,
            Config.TIDAL_ATMOS_MOBILE_TOKEN
        )

        await edit_message(
            cb.message,
            L.TIDAL_AUTH_URL.format(auth_url),
            tidal_auth_buttons()
        )

        sub = await tidalapi.login_tv()

        if sub:
            bot_settings.clients.append(tidalapi)

            await bot_settings.save_tidal_login(tidalapi.tv_session)

            hires = True if tidalapi.mobile_hires else False
            atmos = True if tidalapi.mobile_atmos else False
            tv = True if tidalapi.tv_session else False
            await edit_message(
                cb.message,
                L.TIDAL_AUTH_PANEL.format(sub, hires, atmos, tv) + '\n' + L.TIDAL_AUTH_SUCCESSFULL,
                tidal_auth_buttons()
            )


@Client.on_callback_query(filters.regex(pattern=r"^tdRemove"))
async def tidal_remove_login_cb(c:Client, cb:CallbackQuery):
    if await check_user(cb.from_user.id, restricted=True):
        settings_db.set_variable("TIDAL_AUTH_DATA", 0, True, None)

        tidalapi.tv_session = None
        tidalapi.mobile_atmos = None
        tidalapi.mobile_hires = None
        tidalapi.sub_type = None
        tidalapi.saved = []

        await tidalapi.session.close()

        await c.answer_callback_query(
            cb.id,
            L.TIDAL_REMOVED_SESSION,
            True
        )

        await tidal_auth_cb(c, cb)

