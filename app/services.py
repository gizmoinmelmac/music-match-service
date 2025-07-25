import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import requests
import re
from fuzzywuzzy import fuzz
from typing import List, Optional
import logging
from .config import settings
from .models import *

logger = logging.getLogger(__name__)

class SpotifyService:
    def __init__(self):
        self.spotify = spotipy.Spotify(
            client_credentials_manager=SpotifyClientCredentials(
                client_id=settings.spotify_client_id,
                client_secret=settings.spotify_client_secret
            )
        )
    
    def test_connection(self) -> bool:
        """Test Spotify API connection"""
        try:
            self.spotify.search(q="test", type="track", limit=1)
            return True
        except Exception as e:
            logger.error(f"Spotify connection test failed: {e}")
            return False
    
    def clean_string(self, s: str) -> str:
        """Clean string for better matching"""
        s = re.sub(r'\(feat\..*?\)|\(featuring.*?\)', '', s, flags=re.IGNORECASE)
        s = re.sub(r'\s+', ' ', s).strip().lower()
        return s
    
    def calculate_relevance_score(self, query: str, title: str, artist: str) -> float:
        """Calculate relevance score for search results"""
        query_clean = self.clean_string(query)
        title_clean = self.clean_string(title)
        artist_clean = self.clean_string(artist)
        
        title_exact_match = query_clean in title_clean or title_clean in query_clean
        artist_match = query_clean in artist_clean or artist_clean in query_clean
        
        title_fuzzy = fuzz.ratio(query_clean, title_clean) / 100
        artist_fuzzy = fuzz.ratio(query_clean, artist_clean) / 100
        combined_fuzzy = fuzz.ratio(query_clean, f"{title_clean} {artist_clean}") / 100
        
        score = 0
        if title_exact_match:
            score += 0.5
        if artist_match:
            score += 0.3
        
        score += (title_fuzzy * 0.4 + artist_fuzzy * 0.2 + combined_fuzzy * 0.3)
        return min(1.0, score)
    
    async def search_mixed(self, query: str, limit: int = 10) -> List[Any]:
        """Search for both tracks and albums, return mixed results"""
        try:
            # Search both tracks and albums
            track_results = self.spotify.search(q=query, type="track", limit=max(5, limit // 2))
            album_results = self.spotify.search(q=query, type="album", limit=max(3, limit // 3))
            
            mixed_results = []
            
            # Process tracks
            for track in track_results['tracks']['items']:
                metadata = TrackMetadata(
                    title=track['name'],
                    artist=", ".join([artist['name'] for artist in track['artists']]),
                    album=track['album']['name'],
                    cover_image=track['album']['images'][0]['url'] if track['album']['images'] else None,
                    duration_ms=track['duration_ms'],
                    isrc=track.get('external_ids', {}).get('isrc'),
                    spotify_id=track['id'],
                    spotify_url=track['external_urls']['spotify'],
                    preview_url=track.get('preview_url'),
                    content_type="track"
                )
                relevance = self.calculate_relevance_score(query, track['name'], track['artists'][0]['name'])
                mixed_results.append((metadata, relevance))
            
            # Process albums
            for album in album_results['albums']['items']:
                metadata = AlbumMetadata(
                    title=album['name'],
                    artist=", ".join([artist['name'] for artist in album['artists']]),
                    cover_image=album['images'][0]['url'] if album['images'] else None,
                    total_tracks=album['total_tracks'],
                    release_date=album['release_date'],
                    spotify_id=album['id'],
                    spotify_url=album['external_urls']['spotify'],
                    content_type="album"
                )
                relevance = self.calculate_relevance_score(query, album['name'], album['artists'][0]['name'])
                mixed_results.append((metadata, relevance))
            
            # Sort by relevance and return top results
            mixed_results.sort(key=lambda x: x[1], reverse=True)
            return [item[0] for item in mixed_results[:limit]]
            
        except Exception as e:
            logger.error(f"Mixed search failed: {e}")
            raise e
    
    async def get_track_metadata(self, spotify_id: str) -> TrackMetadata:
        """Get detailed track metadata"""
        try:
            track = self.spotify.track(spotify_id)
            return TrackMetadata(
                title=track['name'],
                artist=", ".join([artist['name'] for artist in track['artists']]),
                album=track['album']['name'],
                cover_image=track['album']['images'][0]['url'] if track['album']['images'] else None,
                duration_ms=track['duration_ms'],
                isrc=track.get('external_ids', {}).get('isrc'),
                spotify_id=track['id'],
                spotify_url=track['external_urls']['spotify'],
                preview_url=track.get('preview_url'),
                content_type="track"
            )
        except Exception as e:
            logger.error(f"Get track metadata failed: {e}")
            raise e
    
    async def get_album_metadata(self, spotify_id: str) -> AlbumMetadata:
        """Get detailed album metadata"""
        try:
            album = self.spotify.album(spotify_id)
            return AlbumMetadata(
                title=album['name'],
                artist=", ".join([artist['name'] for artist in album['artists']]),
                cover_image=album['images'][0]['url'] if album['images'] else None,
                total_tracks=album['total_tracks'],
                release_date=album['release_date'],
                spotify_id=album['id'],
                spotify_url=album['external_urls']['spotify'],
                content_type="album"
            )
        except Exception as e:
            logger.error(f"Get album metadata failed: {e}")
            raise e

class SongLinkService:
    def __init__(self):
        self.base_url = "https://api.song.link/v1-alpha.1"
    
    async def get_platform_links(self, spotify_url: str) -> DSPLinks:
        """Get basic platform links"""
        try:
            api_url = f"{self.base_url}/links?url={spotify_url}"
            response = requests.get(api_url, timeout=10)
            
            if response.status_code != 200:
                logger.warning(f"SongLink API error: {response.status_code}")
                return DSPLinks(spotify=spotify_url)
            
            data = response.json()
            links = data.get('linksByPlatform', {})
            
            return DSPLinks(
                spotify=links.get('spotify', {}).get('url', spotify_url),
                apple_music=links.get('appleMusic', {}).get('url'),
                youtube_music=links.get('youtubeMusic', {}).get('url'),
                deezer=links.get('deezer', {}).get('url'),
                soundcloud=links.get('soundcloud', {}).get('url'),
                amazon_music=links.get('amazonMusic', {}).get('url'),
                tidal=links.get('tidal', {}).get('url')
            )
            
        except Exception as e:
            logger.error(f"SongLink API error: {e}")
            return DSPLinks(spotify=spotify_url)
    
    async def get_detailed_platform_data(self, spotify_url: str) -> DetailedPlatformLinks:
        """Get detailed platform data with deep links"""
        try:
            api_url = f"{self.base_url}/links?url={spotify_url}"
            response = requests.get(api_url, timeout=10)
            
            if response.status_code != 200:
                return DetailedPlatformLinks(
                    spotify=PlatformInfo(url=spotify_url)
                )
            
            data = response.json()
            links = data.get('linksByPlatform', {})
            
            return DetailedPlatformLinks(
                spotify=PlatformInfo(
                    url=links.get('spotify', {}).get('url'),
                    native_app_uri=links.get('spotify', {}).get('nativeAppUriMobile')
                ),
                apple_music=PlatformInfo(
                    url=links.get('appleMusic', {}).get('url'),
                    native_app_uri=links.get('appleMusic', {}).get('nativeAppUriMobile')
                ),
                youtube_music=PlatformInfo(
                    url=links.get('youtubeMusic', {}).get('url'),
                    native_app_uri=links.get('youtubeMusic', {}).get('nativeAppUriMobile')
                ),
                deezer=PlatformInfo(
                    url=links.get('deezer', {}).get('url'),
                    native_app_uri=links.get('deezer', {}).get('nativeAppUriMobile')
                ),
                amazon_music=PlatformInfo(
                    url=links.get('amazonMusic', {}).get('url'),
                    native_app_uri=links.get('amazonMusic', {}).get('nativeAppUriMobile')
                ),
                tidal=PlatformInfo(
                    url=links.get('tidal', {}).get('url'),
                    native_app_uri=links.get('tidal', {}).get('nativeAppUriMobile')
                )
            )
            
        except Exception as e:
            logger.error(f"Detailed platform data error: {e}")
            return DetailedPlatformLinks(spotify=PlatformInfo(url=spotify_url))
    
    async def get_songlink_page_url(self, spotify_url: str) -> str:
        """Get SongLink shareable page URL"""
        try:
            api_url = f"{self.base_url}/links?url={spotify_url}"
            response = requests.get(api_url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return data.get('pageUrl', f"https://song.link/{spotify_url}")
            else:
                return f"https://song.link/{spotify_url}"
                
        except Exception as e:
            logger.error(f"SongLink page URL error: {e}")
            return f"https://song.link/{spotify_url}"