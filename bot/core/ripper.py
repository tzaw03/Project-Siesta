import asyncio
import math
import re

from pathlib import Path
from pyrogram.types import Message

from bot import Config, LOGGER
from bot.models.task import TaskDetails
from bot.models.provider import Provider
from bot.models.metadata import *
from bot.models.errors import MetadataTypeError

from bot.providers.tidal.handler import TidalHandler
from bot.providers.qobuz.handler import QobuzHandler
from bot.providers.deezer.handler import DeezerHandler

from bot.uploader import TelegramUploader, get_uploader
from bot.settings import bot_settings

from bot.utils.message import edit_message, send_art_post
from bot.utils.string import format_progress_message, format_string
from bot.utils.zip import ZipHandler

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
        
        # Apply FFmpeg conversion if enabled
        track_path = await cls.convert_with_ffmpeg(track_path)
   
        uploader = get_uploader()
        await uploader.upload(task_details, track_path, metadata)


    @classmethod
    async def handle_album(cls, item_id, provider: type[Provider], task_details: TaskDetails):
        metadata = await provider.get_album_metadata(item_id, task_details)
        album_path = cls.get_album_dir(task_details, metadata)

        if bot_settings.art_poster:
            await send_art_post(metadata, task_details)

        # albums downloads are always parallel except Telegram downloads
        tasks = []
        for track in metadata.tracks:
            track_path = album_path / format_string("track", track)
            tasks.append(provider.download_track(track, task_details, track_path))
        
        uploader = get_uploader()

        # For telegram runs 
        if uploader == TelegramUploader and not ZipHandler.should_zip(metadata):
            i, l = 0, len(tasks)
            for task, track in zip(tasks, metadata.tracks):
                bar = _progress_bar(i, l)
                await edit_message(task_details.bot_msg, format_progress_message(bar, i, l, metadata.title, 'Album Tracks'), flood_wait=False)
                track_path = await task

                track_path = await cls.convert_with_ffmpeg(track_path)

                await uploader.upload(task_details, track_path, track)
                i+=1
        else:
            # concurrent downloads
            await cls._run_concurrent_tasks(tasks, metadata.title, True, task_details.bot_msg)
            await uploader.upload(task_details, album_path, metadata)


    @classmethod
    async def handle_artist(cls, item_id, provider: type[Provider], task_details: TaskDetails):
        metadata = await provider.get_artist_metadata(item_id, task_details)
        artist_path = cls.get_artist_dir(task_details, metadata)

        uploader = get_uploader()

        i, l = 0, len(metadata.albums)
        for album in metadata.albums:
            album_path = artist_path / format_string('album', album)
            
            if bot_settings.art_poster:
                await send_art_post(album, task_details)

            bar = _progress_bar(i, l)
            await edit_message(task_details.bot_msg, format_progress_message(bar, i, l, metadata.artist, 'Artist Albums'), flood_wait=False)
            
            tasks = []
            for track in album.tracks:
                track_path = album_path / format_string("track", track)
                tasks.append(provider.download_track(track, task_details, track_path))

            # similar to the album logic, telegram downloads are sequential
            if uploader == TelegramUploader and not ZipHandler.should_zip(metadata):
                for task, track in zip(tasks, album.tracks):
                    track_path = await task
                    track_path = await cls.convert_with_ffmpeg(track_path)
                    await uploader.upload(task_details, track_path, track)
            else:
                # concurrent downloads
                await cls._run_concurrent_tasks(tasks, metadata.title, False, task_details.bot_msg)
                if bot_settings.artist_batch is False:
                    await uploader.upload(task_details, album_path, album)
            i+=1

        if bot_settings.artist_batch:
            await uploader.upload(task_details, artist_path, metadata)


    @classmethod
    async def handle_playlist(cls, item_id, provider: type[Provider], task_details: TaskDetails):
        metadata = await provider.get_playlist_metadata(item_id, task_details)
        playlist_path = cls.get_playlist_dir(task_details, metadata)

        if bot_settings.art_poster:
            await send_art_post(metadata, task_details)

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
                track_path = await cls.convert_with_ffmpeg(track_path)
                await uploader.upload(task_details, track_path, track)
                i+=1
        else:
            results = await cls._run_concurrent_tasks(tasks, metadata.title, True, task_details.bot_msg)
            
            if ZipHandler.should_zip(metadata) and not bot_settings.playlist_sort:
                 await uploader.upload(task_details, playlist_path, metadata)
            else:
                for track_path, track in zip(results, metadata.tracks):
                    if track_path: # Ensure download was successful
                        track_path = await cls.convert_with_ffmpeg(track_path)
                        await uploader.upload(task_details, track_path, track)




    @classmethod
    async def _run_concurrent_tasks(cls, tasks: list, title, show_progress:bool, bot_msg=Optional[Message]):
        semaphore = asyncio.Semaphore(Config.MAX_WORKERS)
        i = [0]
        l = len(tasks)
        async def sem_task(task):
            async with semaphore:
                result = await task

                if result:
                    result = await cls.convert_with_ffmpeg(result)

                if show_progress and result:
                    i[0]+=1 # currently done
                    bar = _progress_bar(i[0], l)
                    await edit_message(bot_msg, format_progress_message(bar, i[0], l, title, 'Album Tracks'), flood_wait=False)
                return result
        return await asyncio.gather(*(sem_task(task) for task in tasks))


    @staticmethod
    async def convert_with_ffmpeg(track_path: Path) -> Path:
        """Convert track using FFmpeg if enabled. Returns the new path if converted, original otherwise."""
        if not Config.FFMPEG_ENABLED or not track_path or not track_path.exists():
            return track_path
        
        try:
            # Extract output extension from the FFmpeg command
            cmd_template = Config.FFMPEG_CMD
            output_ext_match = re.search(r'\{output\}', cmd_template)
            
            if not output_ext_match:
                return track_path
            
            if 'libmp3lame' in cmd_template or 'mp3' in cmd_template.lower():
                output_ext = '.mp3'
            elif 'libopus' in cmd_template or 'opus' in cmd_template.lower():
                output_ext = '.opus'
            elif 'libvorbis' in cmd_template or 'ogg' in cmd_template.lower():
                output_ext = '.ogg'
            elif 'aac' in cmd_template.lower() or 'libfdk_aac' in cmd_template:
                output_ext = '.m4a'
            elif 'flac' in cmd_template.lower():
                output_ext = '.flac'
            elif 'alac' in cmd_template.lower():
                output_ext = '.m4a'
            elif 'libwavpack' in cmd_template.lower() or 'wavpack' in cmd_template.lower():
                output_ext = '.wv'
            else:
                output_ext = '.mp3'
            
            input_path = track_path
            output_path = track_path.with_suffix(output_ext + '.tmp')
            
            cmd = cmd_template.format(
                input=f'"{input_path}"',
                output=f'"{output_path}"'
            )
            
            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                # FFmpeg failed, log error and return original path
                LOGGER.error(f"FFmpeg conversion failed: {stderr.decode()}")
                if output_path.exists():
                    output_path.unlink()
                return track_path
            
            # Remove original file and rename converted file
            input_path.unlink()
            final_path = track_path.with_suffix(output_ext)
            output_path.rename(final_path)
            
            return final_path
            
        except Exception as e:
            LOGGER.error(f"FFmpeg conversion error: {e}")
            return track_path




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