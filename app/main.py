from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import time
import logging
from .models import *
from .services import SpotifyService, SongLinkService
from .config import settings

# Configure logging
logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Music Booster Service",
    description="Search music and get cross-platform streaming links",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
spotify_service = SpotifyService()
songlink_service = SongLinkService()

# Middleware for request timing
@app.middleware("http")
async def add_process_time_header(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    logger.info(f"{request.method} {request.url.path} - {process_time:.3f}s")
    return response

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    try:
        # Test Spotify connection
        spotify_status = spotify_service.test_connection()
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "services": {
                "spotify": "up" if spotify_status else "down",
                "songlink": "up"  # No auth required, assume up
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")

# Search endpoint
@app.post("/search", response_model=SearchResponse)
async def search_music(request: SearchRequest):
    """Search for music - returns mixed results (tracks + albums)"""
    try:
        logger.info(f"Searching for: {request.query}")
        
        results = await spotify_service.search_mixed(request.query, request.limit)
        
        return SearchResponse(
            query=request.query,
            total_results=len(results),
            results=results
        )
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

# Cross-platform matching
@app.post("/match/{spotify_id}", response_model=MatchResult)
async def match_across_platforms(spotify_id: str, content_type: str = "track"):
    """Get cross-platform links for a Spotify track or album"""
    try:
        logger.info(f"Matching {content_type}: {spotify_id}")
        
        # Get metadata from Spotify
        if content_type == "track":
            metadata = await spotify_service.get_track_metadata(spotify_id)
        else:
            metadata = await spotify_service.get_album_metadata(spotify_id)
        
        # Get cross-platform links
        platform_links = await songlink_service.get_platform_links(metadata.spotify_url)
        
        # Calculate confidence score
        platform_count = sum([
            1 for link in [
                platform_links.apple_music, platform_links.youtube_music,
                platform_links.deezer, platform_links.amazon_music,
                platform_links.tidal, platform_links.soundcloud
            ] if link
        ])
        confidence_score = min(0.95, 0.5 + (platform_count * 0.08))
        
        return MatchResult(
            metadata=metadata.dict(),
            dsp_links=platform_links,
            confidence_score=confidence_score,
            content_type=content_type
        )
        
    except Exception as e:
        logger.error(f"Matching failed: {e}")
        raise HTTPException(status_code=500, detail=f"Matching failed: {str(e)}")

# Rich landing page data
@app.get("/landing/{spotify_id}", response_model=LandingPageData)
async def get_landing_page_data(spotify_id: str):
    """Get comprehensive data for custom landing pages"""
    try:
        logger.info(f"Getting landing data for: {spotify_id}")
        
        # Get rich metadata
        metadata = await spotify_service.get_track_metadata(spotify_id)
        
        # Get all platform links with deep linking
        platform_data = await songlink_service.get_detailed_platform_data(metadata.spotify_url)
        
        # Get SongLink page info
        songlink_page = await songlink_service.get_songlink_page_url(metadata.spotify_url)
        
        return LandingPageData(
            title=metadata.title,
            artist=metadata.artist,
            album=metadata.album,
            thumbnail_small=metadata.cover_image,  # Could implement multiple sizes
            thumbnail_medium=metadata.cover_image,
            thumbnail_large=metadata.cover_image,
            platforms=platform_data,
            songlink_page_url=songlink_page,
            duration_ms=metadata.duration_ms,
            isrc=metadata.isrc,
            release_date=getattr(metadata, 'release_date', None),
            popularity=getattr(metadata, 'popularity', None),
            preview_url=metadata.preview_url,
            spotify_id=spotify_id
        )
        
    except Exception as e:
        logger.error(f"Landing page data failed: {e}")
        raise HTTPException(status_code=500, detail=f"Landing page data failed: {str(e)}")

# Optimized preview card data
@app.get("/preview-card/{spotify_id}", response_model=PreviewCardData)
async def get_preview_card_data(spotify_id: str):
    """Get optimized data for preview cards/widgets"""
    try:
        landing_data = await get_landing_page_data(spotify_id)
        
        return PreviewCardData(
            title=landing_data.title,
            artist=landing_data.artist,
            album=landing_data.album,
            cover_art=landing_data.thumbnail_medium,
            duration=f"{landing_data.duration_ms // 60000}:{(landing_data.duration_ms % 60000) // 1000:02d}" if landing_data.duration_ms else None,
            preview_url=landing_data.preview_url,
            quick_links={
                "spotify": landing_data.platforms.spotify.url if landing_data.platforms.spotify else None,
                "apple_music": landing_data.platforms.apple_music.url if landing_data.platforms.apple_music else None,
                "youtube_music": landing_data.platforms.youtube_music.url if landing_data.platforms.youtube_music else None,
                "deezer": landing_data.platforms.deezer.url if landing_data.platforms.deezer else None
            },
            deep_links={
                "spotify_app": landing_data.platforms.spotify.native_app_uri if landing_data.platforms.spotify else None,
                "apple_music_app": landing_data.platforms.apple_music.native_app_uri if landing_data.platforms.apple_music else None
            }
        )
        
    except Exception as e:
        logger.error(f"Preview card failed: {e}")
        raise HTTPException(status_code=500, detail=f"Preview card failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.api_port)