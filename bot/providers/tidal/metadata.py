from datetime import datetime

from ...models.metadata import TrackMetadata, AlbumMetadata, ArtistMetadata, PlaylistMetadata
from ...utils.downloader import downloader
from ...models.provider import MetadataHandler

class TidalMetadata(MetadataHandler):
    
    @classmethod
    async def process_track_metadata(cls, track_id, track_data, cover_folder):
        metadata = TrackMetadata(
            itemid=track_id,
            title=track_data['title'],
            copyright=track_data['copyright'],
            albumartist=track_data['artist']['name'],
            artist=cls.get_artists_name(track_data),
            album=track_data['album']['title'],
            isrc=track_data['isrc'],
            duration=track_data['duration'],
            explicit=track_data['explicit'],
            tracknumber=track_data['trackNumber'],
            provider='tidal'
        )

        if track_data['version']:
            metadata.title += f' ({track_data["version"]})'

        parsed_date = datetime.strptime(track_data['streamStartDate'], '%Y-%m-%dT%H:%M:%S.%f%z')
        metadata.date = str(parsed_date.date())
        metadata.cover = await cls.get_cover(track_data['album'].get('cover', ''), cover_folder)
        metadata.thumbnail = await cls.get_cover(track_data['album'].get('cover', ''), cover_folder, 'thumbnail')

        metadata._extra['media_tags'] = track_data['mediaMetadata']['tags']

        return metadata


    @classmethod
    async def process_album_metadata(cls, album_id, album_data, track_datas, cover_folder):
        metadata = AlbumMetadata(
            itemid=album_id,
            albumartist=album_data['artist']['name'],
            upc=album_data['upc'],
            title=album_data['title'],
            album=album_data['title'],
            date=album_data['releaseDate'],
            totaltracks=album_data['numberOfTracks'],
            duration=album_data['duration'],
            copyright=album_data['copyright'],
            explicit=album_data['explicit'],
            totalvolume=album_data['numberOfVolumes'],
            provider='tidal'
        )

        if album_data['version']:
            metadata.title += f' ({album_data["version"]})'

        metadata.artist = cls.get_artists_name(album_data)
        metadata.cover = await cls.get_cover(album_data.get('cover', ''), cover_folder)
        metadata.thumbnail = await cls.get_cover(album_data.get('cover', ''), cover_folder, 'thumbnail')

        for track in track_datas:
            track_meta = await cls.process_track_metadata(track['id'], track, cover_folder)
            metadata.tracks.append(track_meta)
        
        return metadata


    @classmethod
    async def process_artist_metadata(cls, artist_data, album_datas, cover_folder):
        metadata = ArtistMetadata(
            title=artist_data['name'],
            artist=artist_data['name'],
            provider='tidal'
        )
        #metadata.cover = await cls.get_cover(artist_data.get('picture', ''), cover_folder, 'artist')
        #metadata.thumbnail = metadata.cover # artist doesnt have much resolution option
        metadata._extra['albums'] = album_datas
        return metadata


    @classmethod
    async def process_playlist_metadata(cls, playlist_data, track_datas, cover_folder):
        metadata = PlaylistMetadata(
            itemid=playlist_data['uuid'],
            title=playlist_data['title'],
            provider='tidal',
            tracks=track_datas,
            totaltracks=playlist_data['numberOfTracks'],
            duration=playlist_data['duration'],
            date=playlist_data['created']
        )

        metadata.cover = await cls.get_cover(playlist_data.get('image'), cover_folder)
        metadata.thumbnail = await cls.get_cover(playlist_data.get('image'), cover_folder, 'thumbnail')
        return metadata

    @staticmethod
    async def get_cover(cover_id, cover_folder, cover_type='track'):
        suffix = ''
        if cover_type == 'thumbnail':
            url = f'https://resources.tidal.com/images/{cover_id.replace("-", "/")}/80x80.jpg'
            suffix = '-thumb'
        elif cover_type == 'artist':
            url = f'https://resources.tidal.com/images/{cover_id.replace("-", "/")}/750x750.jpg'
        else:
            url = f'https://resources.tidal.com/images/{cover_id.replace("-", "/")}/1280x1280.jpg'
        return await downloader.create_cover_file(url, cover_id, cover_folder, suffix)


    @staticmethod
    def get_artists_name(meta:dict):
        artists = []
        for a in meta['artists']:
            artists.append(a['name'])
        return ', '.join([str(artist) for artist in artists])