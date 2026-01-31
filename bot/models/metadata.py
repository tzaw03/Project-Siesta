from dataclasses import dataclass, field
from typing import Optional, Any, Union
from pathlib import Path


@dataclass
class _Metadata:
    itemid: str = 0
    title: str = ''
    provider: str = ''
    cover: Optional[Path] = None
    thumbnail: Optional[Path] = None


@dataclass
class _AudioMetadata(_Metadata):
    album: str = ''
    artist: str = ''
    duration: int = 0
    lyrics: str = ''
    tracknumber: int = 0
    totaltracks: int = 1
    albumartist: str = ''
    quality: str = ''
    explicit: str = ''
    genre: str = ''
    copyright: str = ''
    date: str = ''
    volume: int = 1
    totalvolume: int = 1
    extension: Optional[str] = None


@dataclass
class TrackMetadata(_AudioMetadata):
    isrc: str = ''
    type_: str = 'track'
    _extra: dict[str, Any] = field(default_factory=dict) # for any extra data needed by provider


@dataclass
class AlbumMetadata(_AudioMetadata):
    upc: str = ''
    tracks: list[TrackMetadata] = field(default_factory=list)
    type_: str = 'album'


@dataclass
class ArtistMetadata(_Metadata):
    artist: str = ''
    albums: list[AlbumMetadata] = field(default_factory=list)
    type_: str = 'artist'
    _extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class PlaylistMetadata(_Metadata):
    tracks: list[TrackMetadata] = field(default_factory=list)
    totaltracks: int = 1
    date: str = ''
    duration: int = 0
    type_: str = 'playlist'


MetadataType = Union[
    TrackMetadata,
    AlbumMetadata,
    ArtistMetadata,
    PlaylistMetadata,
]