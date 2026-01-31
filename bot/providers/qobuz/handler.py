import re

from bot.models.errors import NotAvailableForDownload
from bot import LOGGER

from bot.models.provider import Provider
from .qopy import qobuz_api
from .metadata import QobuzMetadata
from bot.utils.downloader import downloader
from bot.utils.message import send_text
from bot.utils.metadata import set_metadata


class QobuzHandler(Provider):

    @staticmethod
    def parse_url(url):
        r = re.search(
            r"(?:https:\/\/(?:w{3}|open|play)\.qobuz\.com)?(?:\/[a-z]{2}-[a-z]{2})"
            r"?\/(album|artist|track|playlist|label|interpreter)(?:\/[-\w\d]+)?\/([\w\d]+)",
            url,
        )
        item_type, item_id = r.groups()
        item_type = 'artist' if item_type == 'interpreter' else item_type
        return item_id, item_type


    @classmethod
    async def get_track_metadata(cls, item_id, task_details):
        stream_data = await qobuz_api.get_track_url(item_id)
        if "sample" not in stream_data and stream_data.get('sampling_rate'):
            raw_data = await qobuz_api.get_track_meta(item_id)
            if not raw_data.get('streamable'):
                raise NotAvailableForDownload
        else:
            raise NotAvailableForDownload

        metadata = await QobuzMetadata.process_track_metadata(item_id, raw_data, task_details.tempfolder)
        return metadata


    @classmethod
    async def get_album_metadata(cls, item_id: str, task_details):
        raw_data = await qobuz_api.get_album_meta(item_id)
        if not raw_data.get('streamable'):
            raise NotAvailableForDownload


        tracks = raw_data['tracks']['items']
        for track in tracks: # inject album data for cached usage of metadata
            track['album'] = raw_data # not memory efficient but better than api calls

        metadata = await QobuzMetadata.process_album_metadata(item_id, raw_data, tracks, task_details.tempfolder)
        return metadata


    @classmethod
    async def get_artist_metadata(cls, item_id, task_details):
        raw_data = await qobuz_api.get_artist_meta(item_id)
        smart_discography = True
        if smart_discography:
            _albums = QobuzHandler.smart_discography_filter(
                raw_data,
                save_space=True,
                skip_extras=True,
            )
        else:
            _albums = [item["albums"]["items"] for item in raw_data][0]

        albums = []
        for item in _albums:
            album = await cls.get_album_metadata(item['id'], task_details)
            albums.append(album)
        
        metadata = await QobuzMetadata.process_artist_metadata(raw_data[0], albums, task_details.tempfolder)
        return metadata


    @classmethod
    async def get_playlist_metadata(cls, item_id, task_details):
        _data = await qobuz_api.get_plist_meta(item_id)
        raw_data = _data[0]

        tracks_data = raw_data['tracks']['items']

        metadata = await QobuzMetadata.process_playlist_metadata(raw_data, tracks_data, task_details.tempfolder)
        return metadata


    @classmethod
    async def download_track(cls, metadata, task_details, download_path):
        raw_data = await qobuz_api.get_track_url(metadata.itemid)
        try:
            url = raw_data['url']
        except Exception as e:
            LOGGER.error(e)
            return

        metadata.extension, metadata.quality, = cls.get_quality(raw_data)
        download_path = download_path.with_suffix(f".{metadata.extension}")

        try:
            await downloader.download_file(url, download_path)
        except Exception as e:
            LOGGER.error(e)
            await send_text(e, task_details)
            return

        await set_metadata(metadata, download_path)
        return download_path



    @staticmethod
    def smart_discography_filter(
        contents: list, save_space: bool = False, skip_extras: bool = False
    ) -> list:

        TYPE_REGEXES = {
            "remaster": r"(?i)(re)?master(ed)?",
            "extra": r"(?i)(anniversary|deluxe|live|collector|demo|expanded)",
        }

        def is_type(album_t: str, album: dict) -> bool:
            """Check if album is of type `album_t`"""
            version = album.get("version", "")
            title = album.get("title", "")
            regex = TYPE_REGEXES[album_t]
            return re.search(regex, f"{title} {version}") is not None

        def essence(album: dict) -> str:
            """Ignore text in parens/brackets, return all lowercase.
            Used to group two albums that may be named similarly, but not exactly
            the same.
            """
            r = re.match(r"([^\(]+)(?:\s*[\(\[][^\)][\)\]])*", album)
            # when the expression is not matched (when paren/bracket exist before title)
            if not r:
                return album.lower()
            return r.group(1).strip().lower()

        requested_artist = contents[0]["name"]
        items = [item["albums"]["items"] for item in contents][0]

        # use dicts to group duplicate albums together by title
        title_grouped = dict()
        for item in items:
            title_ = essence(item["title"])
            if title_ not in title_grouped:  # ?
                #            if (t := essence(item["title"])) not in title_grouped:
                title_grouped[title_] = []
            title_grouped[title_].append(item)

        items = []
        for albums in title_grouped.values():
            best_bit_depth = max(a["maximum_bit_depth"] for a in albums)
            get_best = min if save_space else max
            best_sampling_rate = get_best(
                a["maximum_sampling_rate"]
                for a in albums
                if a["maximum_bit_depth"] == best_bit_depth
            )
            remaster_exists = any(is_type("remaster", a) for a in albums)

            def is_valid(album: dict) -> bool:
                return (
                    album["maximum_bit_depth"] == best_bit_depth
                    and album["maximum_sampling_rate"] == best_sampling_rate
                    and album["artist"]["name"] == requested_artist
                    and not (  # states that are not allowed
                        (remaster_exists and not is_type("remaster", album))
                        or (skip_extras and is_type("extra", album))
                    )
                )

            filtered = tuple(filter(is_valid, albums))
            # most of the time, len is 0 or 1.
            # if greater, it is a complete duplicate,
            # so it doesn't matter which is chosen
            if len(filtered) >= 1:
                items.append(filtered[0])

        return items


    @staticmethod
    def get_quality(meta:dict):
        """
        Args
            meta : track url metadata dict
        Returns
            extention, quality
        """
        if qobuz_api.quality == 5:
            return 'mp3', '320K'
        else:
            return 'flac', f'{meta["bit_depth"]}B - {meta["sampling_rate"]}k'