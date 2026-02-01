from bot.models.metadata import TrackMetadata, AlbumMetadata, ArtistMetadata, PlaylistMetadata
from bot.utils.downloader import downloader
from bot.models.provider import MetadataHandler

from bot.providers.deezer.deezer_api import deezerapi
from bot.providers.deezer.errors import TrackNotAvailable, RegionLocked, FormatNotAvailable


class DeezerMetadata(MetadataHandler):

    @classmethod
    async def process_track_metadata(cls, track_id, track_data, cover_folder):
        t_meta = track_data.get('FALLBACK', track_data)
        
        metadata = TrackMetadata(
            itemid=str(track_id),
            title=t_meta['SNG_TITLE'],
            copyright=t_meta.get('COPYRIGHT', ''),
            albumartist=t_meta['ART_NAME'],
            artist=cls.get_artists_name(t_meta),
            album=t_meta['ALB_TITLE'],
            isrc=t_meta.get('ISRC', ''),
            duration=int(t_meta['DURATION']),
            tracknumber=int(t_meta.get('TRACK_NUMBER', 1)),
            date=t_meta.get('PHYSICAL_RELEASE_DATE', ''),
            provider='deezer'
        )

        if t_meta.get('VERSION'):
            metadata.title += f' ({t_meta["VERSION"]})'

        explicit_info = t_meta.get('EXPLICIT_TRACK_CONTENT', {})
        if explicit_info.get('EXPLICIT_LYRICS_STATUS'):
            metadata.explicit = str(explicit_info['EXPLICIT_LYRICS_STATUS'])

        metadata.cover = await cls.get_cover(t_meta.get('ALB_PICTURE'), cover_folder, 'track')
        metadata.thumbnail = await cls.get_cover(t_meta.get('ALB_PICTURE'), cover_folder, 'thumbnail')

        # Store extra data needed for download
        metadata._extra['token'] = t_meta['TRACK_TOKEN']
        metadata._extra['token_expiry'] = t_meta['TRACK_TOKEN_EXPIRE']
        metadata._extra['quality'] = await cls.get_quality(t_meta)

        return metadata


    @classmethod
    async def process_album_metadata(cls, album_id, album_data, track_datas, cover_folder):
        """
        Process album metadata from raw Deezer album data.
        
        Args:
            album_id: Album ID from Deezer
            album_data: Raw album data dict (DATA section)
            track_datas: List of track data dicts
            cover_folder: Path to save cover files
        """
        metadata = AlbumMetadata(
            itemid=str(album_id),
            title=album_data['ALB_TITLE'],
            albumartist=album_data['ART_NAME'],
            upc=album_data.get('UPC', ''),
            album=album_data['ALB_TITLE'],
            artist=cls.get_artists_name(album_data),
            date=album_data.get('DIGITAL_RELEASE_DATE', ''),
            totaltracks=int(album_data.get('NUMBER_TRACK', 0)),
            duration=int(album_data.get('DURATION', 0)),
            copyright=album_data.get('COPYRIGHT', ''),
            provider='deezer'
        )

        if album_data.get('VERSION'):
            metadata.title += f' ({album_data["VERSION"]})'

        metadata.cover = await cls.get_cover(album_data.get('ALB_PICTURE'), cover_folder, 'track')
        metadata.thumbnail = await cls.get_cover(album_data.get('ALB_PICTURE'), cover_folder, 'thumbnail')

        # Process tracks
        for track in track_datas:
            track_meta = await cls.process_track_metadata(
                track['SNG_ID'],
                track,
                cover_folder
            )
            metadata.tracks.append(track_meta)

        if metadata.tracks:
            metadata.quality = metadata.tracks[0]._extra.get('quality', '')

        return metadata


    @classmethod
    async def process_artist_metadata(cls, artist_data, album_datas, cover_folder):
        metadata = ArtistMetadata(
            itemid=str(artist_data.get('ART_ID', '')),
            title=artist_data.get('ART_NAME', ''),
            artist=artist_data.get('ART_NAME', ''),
            provider='deezer',
            albums=album_datas
        )

        art_picture = artist_data.get('ART_PICTURE')
        if art_picture:
            metadata.cover = await cls.get_cover(art_picture, cover_folder, 'artist')
            metadata.thumbnail = metadata.cover

        return metadata


    @classmethod
    async def process_playlist_metadata(cls, playlist_data, track_datas, cover_folder):
        metadata = PlaylistMetadata(
            itemid=str(playlist_data.get('PLAYLIST_ID', '')),
            title=playlist_data.get('TITLE', ''),
            provider='deezer',
            tracks=track_datas,
            totaltracks=int(playlist_data.get('NB_SONG', 0)),
            duration=int(playlist_data.get('DURATION', 0))
        )

        metadata.cover = await cls.get_cover(playlist_data.get('PLAYLIST_PICTURE'), cover_folder, 'track')
        metadata.thumbnail = await cls.get_cover(playlist_data.get('PLAYLIST_PICTURE'), cover_folder, 'thumbnail')

        return metadata


    @staticmethod
    async def get_cover(cover_id, cover_folder, cover_type='track'):
        if not cover_id:
            return None

        suffix = ''
        if cover_type == 'thumbnail':
            url = f'https://cdn-images.dzcdn.net/images/cover/{cover_id}/80x0-none-100-0-0.png'
            suffix = '-thumb'
        elif cover_type == 'artist':
            url = f'https://cdn-images.dzcdn.net/images/artist/{cover_id}/750x0-none-100-0-0.png'
        else:
            url = f'https://cdn-images.dzcdn.net/images/cover/{cover_id}/3000x0-none-100-0-0.png'

        return await downloader.create_cover_file(url, cover_id, cover_folder, suffix)


    @staticmethod
    def get_artists_name(meta: dict) -> str:
        artists = []
        if 'ARTISTS' in meta:
            for a in meta['ARTISTS']:
                artists.append(a['ART_NAME'])
        elif 'ART_NAME' in meta:
            artists.append(meta['ART_NAME'])
        return ', '.join([str(artist) for artist in artists])


    @staticmethod
    async def get_quality(meta: dict) -> str:
        format = 'FLAC'
        premium_formats = ['FLAC', 'MP3_320']
        countries = meta.get('AVAILABLE_COUNTRIES', {}).get('STREAM_ADS')
        
        if not countries:
            raise TrackNotAvailable()
        elif deezerapi.country not in countries:
            raise RegionLocked()
        else:
            formats_to_check = premium_formats.copy()
            while len(formats_to_check) != 0:
                if formats_to_check[0] != format:
                    formats_to_check.pop(0)
                else:
                    break

            temp_f = None
            for f in formats_to_check:
                if meta.get(f'FILESIZE_{f}', '0') != '0':
                    temp_f = f
                    break
            if temp_f is None:
                temp_f = 'MP3_128'
            format = temp_f

            if format not in deezerapi.available_formats:
                raise FormatNotAvailable()

        return format
