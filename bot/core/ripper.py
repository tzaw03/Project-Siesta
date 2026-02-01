import asyncio
import math

from pyrogram.types import Message

from bot import Config

from ..models.task import TaskDetails
from ..models.provider import Provider
from ..models.metadata import *
from ..models.errors import MetadataTypeError

from bot.providers.tidal.handler import TidalHandler
from bot.providers.qobuz.handler import QobuzHandler
from bot.providers.deezer.handler import DeezerHandler

from .uploader import TelegramUploader, get_uploader
from ..settings import bot_settings

from ..utils.message import edit_message
from ..utils.string import format_progress_message, format_string
from ..utils.zip import ZipHandler

PROVIDERS = {
    'tidal': TidalHandler,
    'qobuz': QobuzHandler,
    'deezer': DeezerHandler
}


def _progress_bar(done, total):
        bar = "{0}{1}".format(
            ''.join(["▰" for i in range(math.floor((done/total) * 10))]),
            ''.join(["▱" for i in range(10 - math.floor((done/total) * 10))])
        )
        return bar


class Ripper:
    @classmethod
    async def start(cls, url: str, task_details: TaskDetails):
        provider = cls._get_provider(url)

        item_id, type_ = provider.parse_url(url)

        if type_ == 'track':
            await cls.handle_track(item_id, provider, task_details)
        elif type_ == 'album':
            await cls.handle_album(item_id, provider, task_details)
        elif type_ == 'artist':
            await cls.handle_artist(item_id, provider, task_details)
        elif type_ == 'playlist':
            await cls.handle_playlist(item_id, provider, task_details)
        else:
            raise MetadataTypeError



    @classmethod
    def _get_provider(cls, url):
        for provider, prefixes in Config.PROVIDERS_LINK_FORMAT.items():
            if url.startswith(prefixes):
                provider_cls = PROVIDERS[provider]
                return provider_cls
        raise Exception('RIPPER: No handlers found for the link')



    @classmethod
    async def handle_track(cls, item_id:str, provider: type[Provider], task_details: TaskDetails):
        metadata = await provider.get_track_metadata(item_id, task_details)
        track_path = cls.get_track_path(task_details, metadata)
        track_path = await provider.download_track(metadata, task_details, track_path)
   
        uploader = get_uploader()
        await uploader.upload(task_details, track_path, metadata)


    @classmethod
    async def handle_album(cls, item_id, provider: type[Provider], task_details: TaskDetails):
        metadata = await provider.get_album_metadata(item_id, task_details)
        album_path = cls.get_album_dir(task_details, metadata)

        tasks = []
        for track in metadata.tracks:
            track_path = album_path / format_string("track", track)
            tasks.append(provider.download_track(track, task_details, track_path))
        
        uploader = get_uploader()
        if uploader == TelegramUploader and not ZipHandler.should_zip(metadata):
            i, l = 0, len(tasks)
            for task, track in zip(tasks, metadata.tracks):
                bar = _progress_bar(i, l)
                await edit_message(task_details.bot_msg, format_progress_message(bar, i, l, metadata.title, 'Album Tracks'), flood_wait=False)
                track_path = await task
                await uploader.upload(task_details, track_path, track)
                i+=1
        else:
            await cls._run_album_tasks(tasks, metadata.title, True, task_details.bot_msg)
            await uploader.upload(task_details, album_path, metadata)


    @classmethod
    async def handle_artist(cls, item_id, provider: type[Provider], task_details: TaskDetails):
        metadata = await provider.get_artist_metadata(item_id, task_details)
        artist_path = cls.get_artist_dir(task_details, metadata)

        uploader = get_uploader()

        i, l = 0, len(metadata.albums)
        for album in metadata.albums:
            album_path = artist_path / format_string('album', album)
            bar = _progress_bar(i, l)
            await edit_message(task_details.bot_msg, format_progress_message(bar, i, l, metadata.artist, 'Artist Albums'), flood_wait=False)
            tasks = []
            for track in album.tracks:
                track_path = album_path / format_string("track", track)
                tasks.append(provider.download_track(track, task_details, track_path))

            if uploader == TelegramUploader and not ZipHandler.should_zip(metadata):
                for task, track in zip(tasks, album.tracks):
                    track_path = await task
                    await uploader.upload(task_details, track_path, track)
            else:
                await cls._run_album_tasks(tasks, metadata.title, False, task_details.bot_msg)
                if bot_settings.artist_batch is False:
                    await uploader.upload(task_details, album_path, album)
            i+=1

        if bot_settings.artist_batch:
            await uploader.upload(task_details, artist_path, metadata)


    @classmethod
    async def handle_playlist(cls, item_id, provider: type[Provider], task_details: TaskDetails):
        metadata = await provider.get_playlist_metadata(item_id, task_details)
        playlist_path = cls.get_playlist_dir(task_details, metadata)

        tasks = []
        for track in metadata.tracks:
            if bot_settings.playlist_sort:
                track_path = cls.get_track_path(task_details, track)
            else:
                track_path = playlist_path / format_string("track", track)
            
            tasks.append(provider.download_track(track, task_details, track_path))
        
        uploader = get_uploader()
        
        if not bot_settings.playlist_conc and not ZipHandler.should_zip(metadata):
            i, l = 0, len(tasks)
            for task, track in zip(tasks, metadata.tracks):
                bar = _progress_bar(i, l)
                await edit_message(task_details.bot_msg, format_progress_message(bar, i, l, metadata.title, 'Playlist Tracks'), flood_wait=False)
                track_path = await task
                await uploader.upload(task_details, track_path, track)
                i+=1
        else:
            results = await cls._run_album_tasks(tasks, metadata.title, True, task_details.bot_msg)
            
            if ZipHandler.should_zip(metadata) and not bot_settings.playlist_sort:
                 await uploader.upload(task_details, playlist_path, metadata)
            else:
                for track_path, track in zip(results, metadata.tracks):
                    if track_path: # Ensure download was successful
                        await uploader.upload(task_details, track_path, track)




    @staticmethod
    async def _run_album_tasks(tasks: list, title, show_progress:bool, bot_msg=Optional[Message]):
        semaphore = asyncio.Semaphore(Config.MAX_WORKERS)
        i = [0]
        l = len(tasks)
        async def sem_task(task):
            async with semaphore:
                result = await task
                if show_progress and result:
                    i[0]+=1 # currently done
                    bar = _progress_bar(i[0], l)
                    await edit_message(bot_msg, format_progress_message(bar, i[0], l, title, 'Album Tracks'), flood_wait=False)
                return result
        return await asyncio.gather(*(sem_task(task) for task in tasks))



    @staticmethod
    def get_track_path(task_details: TaskDetails, track: TrackMetadata) -> Path:
        """Generate the full path for a track file (without extension)."""
        artist = format_string('artist', track)
        album = format_string('album', track)
        track_name = format_string('track', track)
        
        path = (
            task_details.dl_folder / 
            track.provider.title() /
            artist / 
            album / 
            f"{track_name}"
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        return path


    @staticmethod
    def get_album_dir(task_details: TaskDetails, album: AlbumMetadata) -> Path:
        """Generate the directory path for an album."""
        artist = format_string('artist', album)
        album_name = format_string('album', album)
        
        path = task_details.dl_folder / album.provider.title() / artist / album_name
        path.mkdir(parents=True, exist_ok=True)
        return path


    @staticmethod
    def get_artist_dir(task_details: TaskDetails, artist: ArtistMetadata) -> Path:
        """Generate the directory path for an artist."""
        artist_name = format_string('artist', artist)
        
        path = task_details.dl_folder / artist.provider.title() / artist_name
        path.mkdir(parents=True, exist_ok=True)
        return path


    @staticmethod
    def get_playlist_dir(task_details: TaskDetails, playlist: PlaylistMetadata) -> Path:
        """Generate the directory path for a playlist."""
        
        path = task_details.dl_folder / playlist.provider.title() / "Playlists" / playlist.title
        path.mkdir(parents=True, exist_ok=True)
        return path