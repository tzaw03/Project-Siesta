# From vitiko98/qobuz-dl
import time
import hashlib
import aiohttp
import aiolimiter

from .bundle import Bundle
from .errors import *

from bot import LOGGER

class QoClient:
    def __init__(self):
        self.id: str
        self.secrets: list
        self.session: aiohttp.ClientSession
        self.ratelimit = aiolimiter.AsyncLimiter(30, 60)
        self.base = "https://www.qobuz.com/api.json/0.2/"
        self.sec = None
        self.quality = 6
        self.active = False
        

    async def api_call(self, epoint, **kwargs):
        if epoint == "user/login":
            if kwargs.get('email'):
                params = {
                    "email": kwargs["email"],
                    "password": kwargs["pwd"],
                    "app_id": self.id,
                }
            else:
                params = {
                    "user_id": kwargs["userid"],
                    "user_auth_token": kwargs["usertoken"],
                    "app_id": self.id,
                }
        elif epoint == "track/get":
            params = {"track_id": kwargs["id"]}
        elif epoint == "album/get":
            params = {"album_id": kwargs["id"]}
        elif epoint == "playlist/get":
            params = {
                "extra": "tracks",
                "playlist_id": kwargs["id"],
                "limit": 500,
                "offset": kwargs["offset"],
            }
        elif epoint == "artist/get":
            params = {
                "app_id": self.id,
                "artist_id": kwargs["id"],
                "limit": 500,
                "offset": kwargs["offset"],
                "extra": "albums",
            }
        elif epoint == "label/get":
            params = {
                "label_id": kwargs["id"],
                "limit": 500,
                "offset": kwargs["offset"],
                "extra": "albums",
            }
        elif epoint == "favorite/getUserFavorites":
            unix = time.time()
            # r_sig = "userLibrarygetAlbumsList" + str(unix) + kwargs["sec"]
            r_sig = "favoritegetUserFavorites" + str(unix) + kwargs["sec"]
            r_sig_hashed = hashlib.md5(r_sig.encode("utf-8")).hexdigest()
            params = {
                "app_id": self.id,
                "user_auth_token": self.uat,
                "type": "albums",
                "request_ts": unix,
                "request_sig": r_sig_hashed,
            }
        elif epoint == "track/getFileUrl":
            unix = time.time()
            track_id = kwargs["id"]
            fmt_id = kwargs["fmt_id"]
            if int(fmt_id) not in (5, 6, 7, 27):
                raise InvalidQualityId()
            r_sig = "trackgetFileUrlformat_id{}intentstreamtrack_id{}{}{}".format(
                fmt_id, track_id, unix, kwargs.get("sec", self.sec)
            )
            r_sig_hashed = hashlib.md5(r_sig.encode("utf-8")).hexdigest()
            params = {
                "request_ts": unix,
                "request_sig": r_sig_hashed,
                "track_id": track_id,
                "format_id": fmt_id,
                "intent": "stream",
            }
        else:
            params = kwargs

        return await self.session_call(epoint, params)

    async def session_call(self, epoint, params):
        async with self.ratelimit:
            async with self.session.get(self.base + epoint, params=params) as r:
                if epoint == "user/login":
                    if r.status in [401, 400]:
                        raise InvalidCredentials('QOBUZ : Invalid Email / User ID given')
                    else:
                        pass
                elif (
                    epoint in ["track/getFileUrl", "favorite/getUserFavorites"]
                    and r.status == 400
                ):
                    raise InvalidCredentials("QOBUZ : Invalid App Secret")
                return await r.json()


    async def multi_meta(self, epoint, key, id, type):
        total = 1
        offset = 0
        while total > 0:
            if type in ["tracks", "albums"]:
                j = await self.api_call(epoint, id=id, offset=offset, type=type)[type]
            else:
                j = await self.api_call(epoint, id=id, offset=offset, type=type)
            if offset == 0:
                yield j
                total = j[key] - 500
            else:
                yield j
                total -= 500
            offset += 500
        

    async def test_secret(self, sec):
        try:
            await self.api_call("track/getFileUrl", id=5966783, fmt_id=5, sec=sec)
            return True
        except:
            return False


    def load_tokens(self):
        bundle = Bundle()
        self.id = str(bundle.get_app_id())
        self.secrets = [
            secret for secret in bundle.get_secrets().values() if secret
        ]


    async def login(self, email, password, type_='mail'):
        self.load_tokens()
        self.session = aiohttp.ClientSession()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:83.0) Gecko/20100101 Firefox/83.0",
                "X-App-Id": self.id,
            }
        )
        if type_ == 'mail':
            usr_info = await self.api_call(
                "user/login", 
                email=email, 
                pwd=password
            )
        else:
            usr_info = await self.api_call(
                "user/login", 
                userid=email, 
                usertoken=password
            )
        if not usr_info["user"]["credential"]["parameters"]:
            raise FreeAccountError()
        self.uat = usr_info["user_auth_token"]
        self.session.headers.update({"X-User-Auth-Token": self.uat})
        self.label = usr_info["user"]["credential"]["parameters"]["short_label"]
        LOGGER.info(f"QOBUZ : Membership Status: {self.label}")
        await self.cfg_setup()


    async def cfg_setup(self):
        for secret in self.secrets:
            # Falsy secrets
            if not secret:
                continue
            if await self.test_secret(secret):
                self.sec = secret
                break
        if self.sec is None:
            raise NoValidSecret()


    async def get_track_url(self, id):
            return await self.api_call("track/getFileUrl", id=id, fmt_id=self.quality)

    async def get_album_meta(self, id):
        return await self.api_call("album/get", id=id)

    async def get_track_meta(self, id):
        return await self.api_call("track/get", id=id)

    async def get_artist_meta(self, id):
        res = []
        async for data in self.multi_meta("artist/get", "albums_count", id, None):
            res.append(data)
        return res
        #return await self.multi_meta("artist/get", "albums_count", id, None)

    async def get_plist_meta(self, id):
        res = []
        async for data in self.multi_meta("playlist/get", "tracks_count", id, None):
            res.append(data)
        return res

    async def get_label_meta(self, id):
        return await self.multi_meta("label/get", "albums_count", id, None)

qobuz_api = QoClient()