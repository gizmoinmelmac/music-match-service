import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Spotify API
    spotify_client_id: str
    spotify_client_secret: str
    
    # Application
    environment: str = "development"
    log_level: str = "INFO"
    api_port: int = 8000
    
    class Config:
        env_file = ".env"

settings = Settings()