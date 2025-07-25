from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from enum import Enum

class ContentType(str, Enum):
    TRACK = "track"
    ALBUM = "album"

class SearchRequest(BaseModel):
    query: str
    limit: int = 10

class TrackMetadata(BaseModel):
    title: str
    artist: str
    album: str
    cover_image: Optional[str]
    duration_ms: int
    isrc: Optional[str]
    spotify_id: str
    spotify_url: str
    preview_url: Optional[str]
    content_type: str = "track"

class AlbumMetadata(BaseModel):
    title: str
    artist: str
    cover_image: Optional[str]
    total_tracks: int
    release_date: str
    spotify_id: str
    spotify_url: str
    content_type: str = "album"

class SearchResponse(BaseModel):
    query: str
    total_results: int
    results: List[Any]  # Mix of TrackMetadata and AlbumMetadata

class PlatformInfo(BaseModel):
    url: Optional[str] = None
    native_app_uri: Optional[str] = None
    country: Optional[str] = "US"

class DetailedPlatformLinks(BaseModel):
    spotify: Optional[PlatformInfo] = None
    apple_music: Optional[PlatformInfo] = None
    youtube_music: Optional[PlatformInfo] = None
    youtube: Optional[PlatformInfo] = None
    deezer: Optional[PlatformInfo] = None
    soundcloud: Optional[PlatformInfo] = None
    amazon_music: Optional[PlatformInfo] = None
    tidal: Optional[PlatformInfo] = None
    pandora: Optional[PlatformInfo] = None

class DSPLinks(BaseModel):
    spotify: Optional[str]
    apple_music: Optional[str]
    youtube_music: Optional[str]
    deezer: Optional[str]
    soundcloud: Optional[str]
    amazon_music: Optional[str]
    tidal: Optional[str]

class MatchResult(BaseModel):
    metadata: Dict[str, Any]
    dsp_links: DSPLinks
    confidence_score: float
    content_type: str

class LandingPageData(BaseModel):
    title: str
    artist: str
    album: Optional[str]
    thumbnail_small: Optional[str]
    thumbnail_medium: Optional[str]
    thumbnail_large: Optional[str]
    platforms: DetailedPlatformLinks
    songlink_page_url: str
    duration_ms: Optional[int]
    isrc: Optional[str]
    release_date: Optional[str]
    popularity: Optional[int]
    preview_url: Optional[str]
    spotify_id: str

class PreviewCardData(BaseModel):
    title: str
    artist: str
    album: Optional[str]
    cover_art: Optional[str]
    duration: Optional[str]
    preview_url: Optional[str]
    quick_links: Dict[str, Optional[str]]
    deep_links: Dict[str, Optional[str]]