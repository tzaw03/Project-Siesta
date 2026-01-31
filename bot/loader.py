import json

from bot import LOGGER, Config

from .helpers.database.pg_impl import settings_db
from .providers.qobuz.qopy import qobuz_api
from .helpers.deezer.dzapi import deezerapi
from .providers.tidal.tidal_api import tidalapi
from .utils.string import decrypt_string



async def load_clients():
    await login_tidal()
    await login_qobuz()
    await login_deezer()




async def login_qobuz():
    if Config.QOBUZ_EMAIL and Config.QOBUZ_PASSWORD:
        user, pwd, type_ = Config.QOBUZ_EMAIL, Config.QOBUZ_PASSWORD, 'mail'
    elif Config.QOBUZ_USER and Config.QOBUZ_TOKEN:
        user, pwd, type_ = Config.QOBUZ_USER, Config.QOBUZ_TOKEN, 'token'
    else: return None

    try:
        await qobuz_api.login(user, pwd, type_)
        quality, _ = settings_db.get_variable("QOBUZ_QUALITY")
        if quality:
            qobuz_api.quality = int(quality)
        qobuz_api.active = True
        return qobuz_api
    except Exception as e:
        await close_session(qobuz_api)
        LOGGER.error(e)


async def login_deezer():
    if not Config.DEEZER_BF_SECRET:
        return LOGGER.error('DEEZER : Check BF_SECRET')
        
    try:
        await deezerapi.setup_session(Config.DEEZER_BF_SECRET)
        if Config.DEEZER_EMAIL and Config.DEEZER_PASSWORD:
            await deezerapi.login_via_email(
                Config.DEEZER_EMAIL,
                Config.DEEZER_PASSWORD
            )
        elif Config.DEEZER_ARL:
            await deezerapi.login_via_arl(Config.DEEZER_ARL)
        else:
            return
        
        return deezerapi
    except Exception as e:
        await close_session(deezerapi)
        LOGGER.error(e)


async def login_tidal():
    data = None
    # Refresh token in env is given preference
    if Config.TIDAL_REFRESH_TOKEN:
        data = {
            'user_id': None, 
            'refresh_token': Config.TIDAL_REFRESH_TOKEN, 
            'country_code': Config.TIDAL_COUNTRY_CODE
        }
        LOGGER.debug("TIDAL: Using refresh token from environment")
    else:
        # Try to get saved authentication data
        _, saved_info = settings_db.get_variable("TIDAL_AUTH_DATA")
        if saved_info:
            try:
                data = json.loads(decrypt_string(saved_info))
                LOGGER.debug("TIDAL: Using saved authentication data from Database")
            except Exception as e:
                LOGGER.error(f"TIDAL: Failed to decrypt/parse saved auth data: {e}")

    if data:
        try:
            await tidalapi.login_from_saved(
                Config.TIDAL_TV_TOKEN,
                Config.TIDAL_TV_SECRET,
                Config.TIDAL_MOBILE_TOKEN,
                Config.TIDAL_ATMOS_MOBILE_TOKEN,
                data
            )
            tidalapi.active = True
            return tidalapi
        except Exception as e:
            LOGGER.error(e)
    else:
        if not Config.TIDAL_TV_SECRET and not Config.TIDAL_TV_TOKEN:
            tidalapi.can_login = False


        
async def close_session(instance):
    try:
        await instance.session.close()
    except: pass