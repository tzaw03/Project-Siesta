import os
import logging
from os import getenv
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
LOGGER = logging.getLogger(__name__)

if not os.environ.get("ENV"):
    load_dotenv('.env', override=True)

class Config(object):
    try:
        TG_BOT_TOKEN = getenv("TG_BOT_TOKEN")
        APP_ID = int(getenv("APP_ID"))
        API_HASH = getenv("API_HASH")
        DATABASE_URL = getenv("DATABASE_URL")
        BOT_USERNAME = getenv("BOT_USERNAME")
        ADMINS = set(int(x) for x in getenv("ADMINS").split())
        
        # MIGRATION: Dump Channel ID (e.g. -100123456789)
        # အကယ်၍ အမြဲတမ်း Channel ထဲပို့ချင်ရင် ဒီမှာ ID ထည့်ထားနိုင်ပါတယ်
        DUMP_CHANNEL = int(getenv("DUMP_CHANNEL", 0)) 
    except Exception as e:
        LOGGER.warning(f"BOT : Essential Configs are missing or invalid: {e}")
        exit(1)

    WORK_DIR = getenv("WORK_DIR", "./bot/")
    DOWNLOADS_FOLDER = getenv("DOWNLOADS_FOLDER", "DOWNLOADS")
    DOWNLOAD_BASE_DIR = WORK_DIR + DOWNLOADS_FOLDER
    LOCAL_STORAGE = getenv("LOCAL_STORAGE", DOWNLOAD_BASE_DIR)
    
    PLAYLIST_NAME_FORMAT = getenv("PLAYLIST_NAME_FORMAT", "{title} - Playlist")
    TRACK_NAME_FORMAT = getenv("TRACK_NAME_FORMAT", "{title} - {artist}")

    RCLONE_CONFIG = getenv("RCLONE_CONFIG", None)
    RCLONE_DEST = getenv("RCLONE_DEST", 'remote:newfolder')
    INDEX_LINK = getenv('INDEX_LINK', None)

    QOBUZ_EMAIL = getenv("QOBUZ_EMAIL", None)
    QOBUZ_PASSWORD = getenv("QOBUZ_PASSWORD", None)
    QOBUZ_USER = getenv("QOBUZ_USER", None)
    QOBUZ_TOKEN = getenv("QOBUZ_TOKEN", None)

    DEEZER_EMAIL = getenv("DEEZER_EMAIL", None)
    DEEZER_PASSWORD = getenv("DEEZER_PASSWORD", None)
    DEEZER_BF_SECRET = getenv("DEEZER_BF_SECRET", None)
    DEEZER_ARL = getenv("DEEZER_ARL", None)

    ENABLE_TIDAL = getenv("ENABLE_TIDAL", None)
    TIDAL_MOBILE = getenv("TIDAL_MOBILE", None)
    TIDAL_MOBILE_TOKEN = getenv("TIDAL_MOBILE_TOKEN", None)
    TIDAL_ATMOS_MOBILE_TOKEN = getenv("TIDAL_ATMOS_MOBILE_TOKEN", None)
    TIDAL_TV_TOKEN = getenv("TIDAL_TV_TOKEN", None)
    TIDAL_TV_SECRET = getenv("TIDAL_TV_SECRET", None)
    TIDAL_CONVERT_M4A = getenv("TIDAL_CONVERT_M4A", False)
    TIDAL_REFRESH_TOKEN = getenv("TIDAL_REFRESH_TOKEN", None)
    TIDAL_COUNTRY_CODE = getenv("TIDAL_COUNTRY_CODE", None)

    MAX_WORKERS = int(getenv("MAX_WORKERS", 5))
