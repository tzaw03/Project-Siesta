import json
import base64

from .tidal_api import tidalapi
from .utils import *
from .metadata import TidalMetadata

from bot import LOGGER

from ...models.provider import Provider

from bot.utils.message import send_text
from bot.utils.downloader import downloader
from bot.utils.metadata import set_metadata
from bot.providers.tidal.errors import RegionLocked




class TidalHandler(Provider):
    @staticmethod
    def parse_url(url):
        patterns = [
            (r"/browse/track/(\d+)", "track"),  # Track from browse
            (r"/browse/artist/(\d+)", "artist"),  # Artist from browse
            (r"/browse/album/(\d+)", "album"),  # Album from browse
            (r"/browse/playlist/([\w-]+)", "playlist"),  # Playlist with numeric or UUID
            (r"/track/(\d+)", "track"),  # Track from listen.tidal.com
            (r"/artist/(\d+)", "artist"),  # Artist from listen.tidal.com
            (r"/playlist/([\w-]+)", "playlist"),  # Playlist with numeric or UUID
            (r"/album/\d+/track/(\d+)", "track"),  # Extract only track ID from album_and_track
            (r"/album/(\d+)", "album"),
        ]
        
        for pattern, type_ in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1), type_
        
        raise Exception("TIDAL: Couldn't recognize the URL")


    @classmethod
    async def get_track_metadata(cls, item_id, task_details):
        raw_data = await tidalapi.get_track(item_id)
        metadata = await TidalMetadata.process_track_metadata(item_id, raw_data, task_details.tempfolder)
        return metadata


    @classmethod
    async def get_album_metadata(cls, item_id: str, task_details):
        raw_data = await tidalapi.get_album(item_id)
        track_datas = await tidalapi.get_album_tracks(item_id)
        metadata = await TidalMetadata.process_album_metadata(item_id, raw_data, track_datas['items'], task_details.tempfolder)
        
        track_id = metadata.tracks[0].itemid
        _track_data = await tidalapi.get_track(track_id)
        _session, _quality = get_stream_session(_track_data)
        _stream_data = await tidalapi.get_stream_url(track_id, _quality, _session)

        metadata.quality, metadata.extension = get_quality(_stream_data)
        return metadata


    @classmethod
    async def get_artist_metadata(cls, item_id, task_details):
        raw_data = await tidalapi.get_artist(item_id)
        _album_datas = await tidalapi.get_artist_albums(item_id)
        _artist_eps = await tidalapi.get_artist_albums_ep_singles(item_id)
        
        album_datas = sort_album_from_artist(_album_datas['items'])
        album_datas.extend(sort_album_from_artist(_artist_eps['items']))
        
        metadata = await TidalMetadata.process_artist_metadata(raw_data, album_datas, task_details.tempfolder)
        
        for album in metadata._extra['albums']:
            album_metadata = await cls.get_album_metadata(album['id'], task_details)
            metadata.albums.append(album_metadata)

        return metadata


    @classmethod
    async def get_playlist_metadata(cls, item_id, task_details):
        raw_data = await tidalapi.get_playlist(item_id)
        raw_tracks = await tidalapi.get_playlist_items(item_id)
        
        tracks = []
        for item in raw_tracks['items']:
            try:
                _track_meta = await cls.get_track_metadata(item['item']['id'], task_details)
                tracks.append(_track_meta)
            except RegionLocked:
                LOGGER.error(f"Tidal : Item in playlist is region locked - {raw_data['title']}")
                continue
        
        metadata = await TidalMetadata.process_playlist_metadata(raw_data, tracks, task_details.tempfolder)
        return metadata


    @classmethod
    async def download_track(cls, metadata, task_details, download_path):
        _session, _quality = get_stream_session(metadata._extra['media_tags'])

        try:
            stream_data = await tidalapi.get_stream_url(metadata.itemid, _quality, _session)
        except Exception as e:
            LOGGER.error(e)
            await send_text(e, task_details)
            return

        metadata.quality, extension = get_quality(stream_data)

        if stream_data['manifestMimeType'] == 'application/dash+xml':
            manifest = base64.b64decode(stream_data['manifest'])
            urls, track_codec = parse_mpd(manifest)
        else:
            manifest = json.loads(base64.b64decode(stream_data['manifest']))
            urls = manifest['urls'][0]

        download_path = download_path.with_suffix(f".{extension}")

        if type(urls) == list:
            i = 0
            temp_files = []
            for url in urls[0]:
                temp_path = download_path.with_name(f"{download_path.name}.{i}")

                try:
                    await downloader.download_file(url, temp_path)
                except Exception as e:
                    LOGGER.error(e)
                    await send_text(e, task_details)
                    return # abort if any one part fails
                i+=1
                temp_files.append(temp_path)
            await merge_tracks(temp_files, download_path)
        else:
            try:
                await downloader.download_file(urls, download_path)
            except Exception as e:
                LOGGER.error(e)
                await send_text(e, task_details)
                return

        await set_metadata(metadata, download_path)
        return download_path


tidal_handler = TidalHandler()