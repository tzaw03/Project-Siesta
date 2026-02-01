import os
from os import getenv
from dotenv import load_dotenv
from pathlib import Path

if not os.environ.get("ENV"):
    load_dotenv('.env', override=True)



BASE_DYNAMIC_VARS = {'RCLONE_CONFIG','RCLONE_DEST','INDEX_LINK',}

TIDAL_VARS = {
    'TIDAL_MOBILE_TOKEN', 'TIDAL_ATMOS_MOBILE_TOKEN',
    'TIDAL_TV_TOKEN', 'TIDAL_TV_SECRET', 'TIDAL_CONVERT_M4A',
    'TIDAL_REFRESH_TOKEN', 'TIDAL_COUNTRY_CODE',
}

QOBUZ_VARS = {'QOBUZ_EMAIL', 'QOBUZ_PASSWORD', 'QOBUZ_USER', 'QOBUZ_TOKEN',}

DEEZER_VARS = {'DEEZER_EMAIL', 'DEEZER_PASSWORD', 'DEEZER_BF_SECRET', 'DEEZER_ARL',}

DYNAMIC_VARS = BASE_DYNAMIC_VARS | TIDAL_VARS | QOBUZ_VARS | DEEZER_VARS


class Config(object):
#--------------------

# MAIN BOT VARIABLES

#--------------------
    try:
        TG_BOT_TOKEN = getenv("TG_BOT_TOKEN")
        APP_ID = int(getenv("APP_ID"))
        API_HASH = getenv("API_HASH")
        DATABASE_URL = getenv("DATABASE_URL")
        BOT_USERNAME = getenv("BOT_USERNAME")
        ADMINS = set(int(x) for x in getenv("ADMINS").split())
    except:
        print("BOT : Essential Configs are missing")
        exit(1)


#--------------------

# BOT WORKING DIRECTORY

#--------------------
    # For pyrogram temp files
    WORK_DIR = getenv("WORK_DIR", "./bot/")
    # Just name of the Downloads Folder
    _DOWNLOADS_FOLDER = getenv("DOWNLOADS_FOLDER", "DOWNLOADS")
    DOWNLOAD_BASE_DIR = Path(WORK_DIR + _DOWNLOADS_FOLDER)
    LOCAL_STORAGE = Path(getenv("LOCAL_STORAGE", DOWNLOAD_BASE_DIR))
#--------------------

# FILE/FOLDER NAMING

#--------------------
    PLAYLIST_NAMING = getenv("PLAYLIST_NAMING", "{title} - Playlist")
    ALBUM_NAMING = getenv("ALBUM_NAMING", "{album}")
    TRACK_NAMING = getenv("TRACK_NAMING", "{title} - {artist}")
    ARTIST_NAMING = getenv("ARTIST_NAMING", "{artist}")
    PROVIDERS_LINK_FORMAT = getenv("PROVIDERS_LINK_FORMAT", {
        "tidal": (
            "https://tidal.com",
            "https://listen.tidal.com",
            "tidal.com",
            "listen.tidal.com",
        ),
        "deezer": (
            "https://link.deezer.com",
            "https://deezer.com",
            "deezer.com",
            "https://www.deezer.com",
            "link.deezer.com",
        ),
        "qobuz": (
            "https://play.qobuz.com",
            "https://open.qobuz.com",
            "https://www.qobuz.com",
        ),
        "spotify": ("https://open.spotify.com",),
    })
#--------------------

# RCLONE / INDEX

#--------------------
    RCLONE_CONFIG = getenv("RCLONE_CONFIG", None)
    # No trailing slashes '/' for both index and rclone_dest
    # Example for RCLONE_DEST : remote:yourfolder
    RCLONE_DEST = getenv("RCLONE_DEST", None)
    INDEX_LINK = getenv('INDEX_LINK', None)
#--------------------

# QOBUZ

#--------------------
    QOBUZ_EMAIL = getenv("QOBUZ_EMAIL", None)
    QOBUZ_PASSWORD = getenv("QOBUZ_PASSWORD", None)
    QOBUZ_USER = getenv("QOBUZ_USER", None)
    QOBUZ_TOKEN = getenv("QOBUZ_TOKEN", None)
#--------------------

# DEEZER

#--------------------
    DEEZER_EMAIL = getenv("DEEZER_EMAIL", None)
    DEEZER_PASSWORD = getenv("DEEZER_PASSWORD", None)
    DEEZER_BF_SECRET = getenv("DEEZER_BF_SECRET", None)
    DEEZER_ARL = getenv("DEEZER_ARL", None)
#--------------------

# TIDAL

#--------------------
    ENABLE_TIDAL = getenv("ENABLE_TIDAL", None)
    TIDAL_MOBILE_TOKEN = getenv("TIDAL_MOBILE_TOKEN", None)
    TIDAL_ATMOS_MOBILE_TOKEN = getenv("TIDAL_ATMOS_MOBILE_TOKEN", None)
    TIDAL_TV_TOKEN = getenv("TIDAL_TV_TOKEN", None)
    TIDAL_TV_SECRET = getenv("TIDAL_TV_SECRET", None)
    TIDAL_CONVERT_M4A = getenv("TIDAL_CONVERT_M4A", False)
    TIDAL_REFRESH_TOKEN = getenv("TIDAL_REFRESH_TOKEN", None)
    TIDAL_COUNTRY_CODE = getenv("TIDAL_COUNTRY_CODE", None) # example CA for Canada
#--------------------

# CONCURRENT

#--------------------
    MAX_WORKERS = int(getenv("MAX_WORKERS", 5))
#--------------------

# COPY MESSAGE

#--------------------
    # Channel/Group ID where uploaded files will be copied to
    # Set to None to disable, or provide a chat ID (e.g., -1001234567890)
    COPY_CHANNEL_ID = int(getenv("COPY_CHANNEL_ID")) if getenv("COPY_CHANNEL_ID") else None
#--------------------

# FFMPEG CONVERSION

#--------------------
    FFMPEG_ENABLED = getenv("FFMPEG_ENABLED", "false").lower() == "true"
    # Example: "ffmpeg -i {input} -b:a 320k {output}" to convert to 320kbps
    FFMPEG_CMD = getenv("FFMPEG_CMD", "ffmpeg -i {input} -c:a libmp3lame -b:a 320k {output}")
