import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', '').replace('postgres://', 'postgresql://') or 'sqlite:///saps.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # File upload settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max
    UPLOAD_FOLDER = 'static/uploads'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}
    
    # Session settings - FIXED TYPO HERE
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)  # Was: PERMANENaT_SESSION_LIFETIME
    
    # Email domain validation
    SAPS_EMAIL_DOMAIN = '@saps.gov.za'
    
    # Security
    SESSION_COOKIE_SECURE = os.environ.get('FLASK_ENV') == 'production'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    @staticmethod
    def init_app(app):
        # Create necessary directories
        for folder in ['static/uploads/suspects', 'static/uploads/documents']:
            os.makedirs(folder, exist_ok=True)