# 🎵 Music Booster Service

A production-ready microservice that converts Spotify tracks into universal music links across all major streaming platforms.

## 🚀 What it does

- **Search** music across Spotify's catalog (tracks + albums)
- **Generate** cross-platform streaming links (Apple Music, YouTube Music, Deezer, Tidal, etc.)
- **Provide** rich metadata with cover art, duration, and deep links
- **Serve** optimized data for both detailed pages and quick music cards

## 📋 Features

✅ **Universal Music Links** - Convert any Spotify track to 7+ streaming platforms  
✅ **Smart Search** - Mixed results with relevance scoring  
✅ **Rich Metadata** - Cover art, duration, ISRC, preview URLs  
✅ **Deep Linking** - Native app URIs for mobile integration  
✅ **Production Ready** - Health checks, logging, error handling  
✅ **Developer Friendly** - Interactive API docs, clear responses  

## 🔧 Quick Start

### Prerequisites
- Python 3.11+
- Spotify Developer Account ([Get credentials here](https://developer.spotify.com/dashboard))

### 1. Clone and Setup
```bash
git clone [your-repo-url]
cd music-booster-service

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your Spotify credentials
SPOTIFY_CLIENT_ID=your_client_id_here
SPOTIFY_CLIENT_SECRET=your_client_secret_here
```

### 3. Run the Service
```bash
# Development mode
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or using Docker
docker-compose up -d
```

### 4. Test the API
- Open http://localhost:8000/docs
- Try the health check: http://localhost:8000/health
- Use the interactive API documentation

## 📖 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Service health and status |
| `/search` | POST | Search music (tracks + albums) |
| `/match/{spotify_id}` | POST | Get all platform links |
| `/landing/{spotify_id}` | GET | Rich data for landing pages |
| `/preview-card/{spotify_id}` | GET | Optimized data for music cards |
| `/docs` | GET | Interactive API documentation |

## 🎯 Usage Examples

### Search Music
```bash
curl -X POST "http://localhost:8000/search" \
     -H "Content-Type: application/json" \
     -d '{"query": "Bad Bunny", "limit": 5}'
```

**Response:**
```json
{
  "query": "Bad Bunny",
  "total_results": 5,
  "results": [
    {
      "title": "NUEVAYoL",
      "artist": "Bad Bunny",
      "album": "DeBÍ TiRAR MáS FOToS",
      "cover_image": "https://i.scdn.co/image/ab67616d0000b273...",
      "spotify_id": "5TFD2bmFKGhoCRbX61nXY5",
      "spotify_url": "https://open.spotify.com/track/5TFD2bmFKGhoCRbX61nXY5",
      "content_type": "track"
    }
  ]
}
```

### Get Cross-Platform Links
```bash
curl -X POST "http://localhost:8000/match/5TFD2bmFKGhoCRbX61nXY5?content_type=track"
```

**Response:**
```json
{
  "metadata": {...},
  "dsp_links": {
    "spotify": "https://open.spotify.com/track/5TFD2bmFKGhoCRbX61nXY5",
    "apple_music": "https://geo.music.apple.com/us/album/_/1787022393...",
    "youtube_music": "https://music.youtube.com/watch?v=WdSGEvDGZAo",
    "deezer": "https://www.deezer.com/track/3171002981",
    "amazon_music": "https://music.amazon.com/albums/B0DR9CQ14V...",
    "tidal": "https://listen.tidal.com/track/409386861"
  },
  "confidence_score": 0.95
}
```

### Get Preview Card Data
```bash
curl "http://localhost:8000/preview-card/5TFD2bmFKGhoCRbX61nXY5"
```

**Response:**
```json
{
  "title": "NUEVAYoL",
  "artist": "Bad Bunny",
  "cover_art": "https://i.scdn.co/image/ab67616d0000b273...",
  "duration": "3:03",
  "quick_links": {
    "spotify": "https://open.spotify.com/track/5TFD2bmFKGhoCRbX61nXY5",
    "apple_music": "https://geo.music.apple.com/us/album/_/1787022393...",
    "youtube_music": "https://music.youtube.com/watch?v=WdSGEvDGZAo",
    "deezer": "https://www.deezer.com/track/3171002981"
  },
  "deep_links": {
    "apple_music_app": "music://itunes.apple.com/us/album/_/1787022393..."
  }
}
```

## 🐳 Docker Deployment

### Development
```bash
docker-compose up -d
```

### Production
```bash
# Build image
docker build -t music-booster-service:latest .

# Run container
docker run -d \
  --name music-booster \
  -p 8000:8000 \
  -e SPOTIFY_CLIENT_ID=your_id \
  -e SPOTIFY_CLIENT_SECRET=your_secret \
  music-booster-service:latest
```

## 🛠️ Frontend Integration

### JavaScript/React Example
```javascript
class MusicBooster {
  constructor(baseUrl = 'http://localhost:8000') {
    this.baseUrl = baseUrl;
  }

  async searchMusic(query, limit = 10) {
    const response = await fetch(`${this.baseUrl}/search`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, limit })
    });
    return response.json();
  }

  async getPreviewCard(spotifyId) {
    const response = await fetch(`${this.baseUrl}/preview-card/${spotifyId}`);
    return response.json();
  }

  async getAllPlatforms(spotifyId) {
    const response = await fetch(`${this.baseUrl}/match/${spotifyId}?content_type=track`, {
      method: 'POST'
    });
    return response.json();
  }
}

// Usage
const musicBooster = new MusicBooster();
const results = await musicBooster.searchMusic('Bad Bunny');
const cardData = await musicBooster.getPreviewCard(results.results[0].spotify_id);
```

### React Component Example
```jsx
function MusicCard({ query }) {
  const [cardData, setCardData] = useState(null);

  useEffect(() => {
    async function loadMusic() {
      const musicBooster = new MusicBooster();
      const searchResults = await musicBooster.searchMusic(query, 1);
      if (searchResults.results.length > 0) {
        const card = await musicBooster.getPreviewCard(searchResults.results[0].spotify_id);
        setCardData(card);
      }
    }
    loadMusic();
  }, [query]);

  if (!cardData) return <div>Loading...</div>;

  return (
    <div className="music-card">
      <img src={cardData.cover_art} alt={cardData.title} />
      <h3>{cardData.title}</h3>
      <p>{cardData.artist} • {cardData.duration}</p>
      <div className="streaming-links">
        {Object.entries(cardData.quick_links).map(([platform, url]) => (
          url && <a key={platform} href={url} target="_blank">{platform}</a>
        ))}
      </div>
    </div>
  );
}
```

## 📊 Response Times & Reliability

- **Search**: < 1 second
- **Platform Matching**: < 2 seconds  
- **Success Rate**: 95%+ for popular tracks
- **Uptime**: 99.9%+ (depends on external APIs)

## 🔐 Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SPOTIFY_CLIENT_ID` | ✅ | Your Spotify app client ID |
| `SPOTIFY_CLIENT_SECRET` | ✅ | Your Spotify app client secret |
| `ENVIRONMENT` | ❌ | `development` or `production` |
| `LOG_LEVEL` | ❌ | `INFO`, `DEBUG`, `WARNING`, `ERROR` |
| `API_PORT` | ❌ | Port to run the service (default: 8000) |

## 🚀 Deployment Options

### Cloud Platforms
- **Heroku**: Use included `Dockerfile`
- **AWS ECS**: Deploy with Docker
- **Google Cloud Run**: Serverless container deployment
- **DigitalOcean App Platform**: Git-based deployment

### Self-Hosted
- **Docker Compose**: Included for easy deployment
- **Kubernetes**: Scale with container orchestration
- **Traditional VPS**: Run with gunicorn + nginx

## 🔍 Monitoring & Health Checks

The service includes built-in health monitoring:

```bash
# Health check endpoint
GET /health

# Response
{
  "status": "healthy",
  "timestamp": 1753466458.856639,
  "services": {
    "spotify": "up",
    "songlink": "up"
  }
}
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Spotify Web API** for music data
- **SongLink API** for cross-platform matching
- **FastAPI** for the excellent web framework

## 🆘 Support

- **Documentation**: http://localhost:8000/docs (when running)
- **Issues**: [GitHub Issues](your-repo-url/issues)
- **API Status**: Check `/health` endpoint

---

**Built with ❤️ for universal music access** 🎵