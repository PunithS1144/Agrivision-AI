import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'agrivasion-plantix-ai-secret-2026')
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    DATABASE_PATH = os.path.join(BASE_DIR, 'database', 'agrivasion.db')
    BACKUP_DIR = os.path.join(BASE_DIR, 'database', 'backups')
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'jfif'}
    
    # Image optimization thresholds (bandwidth saving for rural 2G/3G mobile networks)
    IMAGE_MAX_DIMENSION = 1600
    IMAGE_JPEG_QUALITY = 85
    IMAGE_WEBP_QUALITY = 80
    
    # Weather config
    WEATHER_API_URL = "https://api.open-meteo.com/v1/forecast"
    DEFAULT_LATITUDE = 12.9716   # Bengaluru coordinates
    DEFAULT_LONGITUDE = 77.5946
    DEFAULT_CITY = "Bengaluru"

    # Rate Limiting & Security (Requests per minute)
    RATE_LIMIT_DEFAULT = int(os.environ.get('RATE_LIMIT_DEFAULT', 120))
    RATE_LIMIT_AUTH = int(os.environ.get('RATE_LIMIT_AUTH', 30))
    RATE_LIMIT_DIAGNOSIS = int(os.environ.get('RATE_LIMIT_DIAGNOSIS', 45))
    TOKEN_EXPIRATION_HOURS = int(os.environ.get('TOKEN_EXPIRATION_HOURS', 72))

    # Caching TTLs in seconds
    CACHE_WEATHER_TTL = 900       # 15 minutes
    CACHE_CROP_CALENDAR_TTL = 3600 # 1 hour
    CACHE_MARKETPLACE_TTL = 1800  # 30 minutes
    CACHE_METRICS_TTL = 30        # 30 seconds

    # Database Pragmas
    DB_BUSY_TIMEOUT_MS = 5000
    DB_CACHE_SIZE_KB = -32000     # 32MB SQLite cache
