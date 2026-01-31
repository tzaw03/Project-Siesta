import re
import hashlib

from bot.models.metadata import TrackMetadata, AlbumMetadata, ArtistMetadata, PlaylistMetadata
from bot.utils.downloader import downloader
from bot.models.provider import MetadataHandler



class QobuzMetadata(MetadataHandler):

    @classmethod
    async def process_track_metadata(cls, track_id, track_data, cover_folder):
        metadata = TrackMetadata(
            itemid=track_id,
            copyright=track_data['copyright'],
            albumartist=track_data['album']['artist']['name'],
            album=track_data['album']['title'],
            isrc=track_data['isrc'],
            title=track_data['title'],
            duration=track_data['duration'],
            explicit=track_data['parental_warning'],
            tracknumber=track_data['track_number'],
            date=track_data['release_date_original'],
            totaltracks=track_data['album']['tracks_count'],
            provider='qobuz'
        )

        metadata.artist = cls.get_artists_name(track_data['album'])
        if track_data['version']:
            metadata.title += f' ({track_data["version"]})'

        metadata.cover = await cls.get_cover(track_data['album']['image']['large'], cover_folder)
        metadata.thumbnail = await cls.get_cover(track_data['album']['image']['thumbnail'], cover_folder)
        return metadata



    @classmethod
    async def process_album_metadata(cls, album_id, album_data, track_datas, cover_folder):
        metadata = AlbumMetadata(
            itemid=album_id,
            title=album_data['title'],
            albumartist=album_data['artist']['name'],
            upc=album_data['upc'],
            album=album_data['title'],
            artist=album_data['artist']['name'],
            date=album_data['release_date_original'],
            totaltracks=album_data['tracks_count'],
            duration=album_data['duration'],
            copyright=album_data.get('copyright', ''),
            genre=album_data['genre']['name'],
            explicit=album_data['parental_warning'],
            provider='qobuz'
        )

        metadata.cover = await cls.get_cover(album_data['image']['large'], cover_folder)
        metadata.thumbnail = await cls.get_cover(album_data['image']['thumbnail'], cover_folder)
        
        tracks = []
        for item in track_datas:
            track = await cls.process_track_metadata(item['id'], item, cover_folder)
            tracks.append(track)
        metadata.tracks = tracks

        return metadata

    
    @classmethod
    async def process_artist_metadata(cls, artist_data, album_datas, cover_folder):
        metadata = ArtistMetadata(
            itemid=artist_data['id'],
            title=artist_data['name'],
            artist=artist_data['name'],
            provider='qobuz',
            albums=album_datas
        )

        metadata.cover = await cls.get_cover(artist_data['image']['large'], cover_folder)
        metadata.thumbnail = await cls.get_cover(artist_data['image']['small'], cover_folder)
        return metadata

        
    @classmethod
    async def process_playlist_metadata(cls, playlist_data, track_datas, cover_folder):
        metadata = PlaylistMetadata(
            itemid=playlist_data['id'],
            title=playlist_data['name'],
            provider='qobuz',
            totaltracks=playlist_data['tracks_count'],
            date=playlist_data['created_at'],
            duration=playlist_data['duration']
        )

        tracks = []
        for item in track_datas:
            track = await cls.process_track_metadata(item['id'], item, cover_folder)
            tracks.append(track)

        

        metadata.tracks = tracks
        metadata.cover = await cls.get_cover(playlist_data['images300'][0], cover_folder)
        metadata.thumbnail = await cls.get_cover(playlist_data['images'][0], cover_folder)
        return metadata



    @staticmethod
    async def get_cover(cover_id, cover_folder, cover_type='track'):
        url = cover_id #qobuz directly gives url
        match = re.search(r"/covers/.+?/.+?/([a-zA-Z0-9]+)-", url)
        if match:
            cover_id = match.group(1)
        else:
            cover_id = hashlib.md5(url.encode()).hexdigest()
        return await downloader.create_cover_file(url, cover_id, cover_folder, '')


    @staticmethod
    def get_artists_name(meta:dict):
        artists = []
        try:
            for a in meta['artists']:
                artists.append(a['name'])
        except:
            artists.append(meta['artist']['name'])
        return ', '.join([str(artist) for artist in artists])