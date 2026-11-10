import os
import hashlib
import hmac

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    # Flask Settings
    SECRET_KEY = os.environ.get('SECRET_KEY', 'wooinhome-super-secret-key-2026-secure')
    
    # Database Settings
    # Supports PostgreSQL (via DATABASE_URL from Railway/Render/Fly.io) or SQLite locally
    DB_URL = os.environ.get('DATABASE_URL', f"sqlite:///{os.path.join(BASE_DIR, 'data', 'wooinhome.db')}")
    # Render uses postgres:// which SQLAlchemy 1.4+ deprecated in favor of postgresql://
    if DB_URL.startswith("postgres://"):
        DB_URL = DB_URL.replace("postgres://", "postgresql://", 1)
    
    SQLALCHEMY_DATABASE_URI = DB_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Uploads & Assets
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
    AUDIO_CACHE_FOLDER = os.path.join(BASE_DIR, 'static', 'audio_cache')
    DATA_FOLDER = os.path.join(BASE_DIR, 'data')
    MAX_CONTENT_LENGTH = 32 * 1024 * 1024  # 32MB Max Upload
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'pdf', 'heic'}

    # Admin Credentials (Default admin/admin888, configurable via ENV)
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
    # Default password hash for 'admin888'
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin888')
    ADMIN_SALT = os.environ.get('ADMIN_SALT', 'wooinhome-hmac-salt')

    # SMTP Settings (can also be saved in SystemSetting DB)
    SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT = int(os.environ.get('SMTP_PORT', '587'))
    SMTP_USER = os.environ.get('SMTP_USER', '')
    SMTP_PASS = os.environ.get('SMTP_PASS', '')
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'wooinhome2015@gmail.com')

    # Cloud Backup (GitHub)
    GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', '')
    GITHUB_REPO = os.environ.get('GITHUB_REPO', '') # e.g. "username/wooinhome-backup"
    GITHUB_BACKUP_BRANCH = os.environ.get('GITHUB_BACKUP_BRANCH', 'cloud-backup')

    # Keep-Alive
    KEEP_ALIVE_URL = os.environ.get('KEEP_ALIVE_URL', '')
    KEEP_ALIVE_INTERVAL = int(os.environ.get('KEEP_ALIVE_INTERVAL', '600')) # 10 minutes

    @staticmethod
    def hash_password(password: str) -> str:
        return hmac.new(
            Config.ADMIN_SALT.encode('utf-8'),
            password.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

    @staticmethod
    def verify_password(provided_password: str, stored_hash: str) -> bool:
        computed = Config.hash_password(provided_password)
        return hmac.compare_digest(computed, stored_hash)

