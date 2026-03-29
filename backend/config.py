"""
Configuration management for Swasthya Sampark application.
Supports environment variables and different deployment environments.
"""
import os
from pathlib import Path

# Try to load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # python-dotenv not installed, use environment variables directly
    pass

# Base directories
BACKEND_DIR = Path(__file__).parent
PROJECT_ROOT = BACKEND_DIR.parent
FRONTEND_DIR = PROJECT_ROOT / 'frontend'

class Config:
    """Base configuration class"""
    # Flask Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-prod')
    DEBUG = os.environ.get('FLASK_DEBUG', '0') == '1'
    TESTING = False
    
    # Server Configuration
    HOST = os.environ.get('HOST', '0.0.0.0')
    PORT = int(os.environ.get('PORT', 5000))
    
    # Database Configuration
    DATABASE_URL = os.environ.get('DATABASE_URL', f'sqlite:///{BACKEND_DIR}/health_system.db')
    DB_PATH = str(BACKEND_DIR / 'health_system.db')
    
    # Firebase Configuration
    FIREBASE_WEB_API_KEY = os.environ.get('FIREBASE_WEB_API_KEY', '')
    FIREBASE_CREDENTIALS_PATH = os.environ.get(
        'FIREBASE_CREDENTIALS_PATH',
        str(BACKEND_DIR / 'pkl' / 'swasthya-sampark-firebase-adminsdk-fbsvc-121be5c997.json')
    )
    
    # OTP Configuration
    OTP_CODE_LENGTH = int(os.environ.get('OTP_CODE_LENGTH', 6))
    OTP_EXPIRY_MINUTES = int(os.environ.get('OTP_EXPIRY_MINUTES', 10))
    
    # File Upload Configuration
    MAX_UPLOAD_SIZE = int(os.environ.get('MAX_UPLOAD_SIZE', 16777216))  # 16MB
    UPLOAD_FOLDER = str(BACKEND_DIR / 'uploads')
    QR_FOLDER = str(FRONTEND_DIR / 'static' / 'qr')
    
    # ML Model Paths
    MODEL_PATH = str(BACKEND_DIR / 'pkl' / 'svm_health_risk_model.pkl')
    EMERGENCY_MODEL_PATH = str(BACKEND_DIR / 'pkl' / 'Logistic_regression_prediction.pkl')
    
    # Flask Template/Static Configuration
    TEMPLATE_FOLDER = str(FRONTEND_DIR / 'templates')
    STATIC_FOLDER = str(FRONTEND_DIR / 'static')
    
    # Session Configuration
    SESSION_COOKIE_SECURE = os.environ.get('PRODUCTION', 'False').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True
    
    # Production-specific settings
    # SECRET_KEY is inherited from Config class which gets it from os.environ
    # We'll validate it at runtime in get_config() instead of at class definition

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True
    DATABASE_URL = 'sqlite:///:memory:'
    DB_PATH = ':memory:'

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config():
    """Get configuration based on environment"""
    env = os.environ.get('FLASK_ENV', 'development')
    config_class = config.get(env, config['default'])
    
    # Validate SECRET_KEY for production
    if env == 'production':
        secret_key = os.environ.get('SECRET_KEY')
        if not secret_key or secret_key == 'dev-secret-key-change-in-prod':
            import warnings
            warnings.warn(
                "SECRET_KEY not set or using default value in production! "
                "Please set SECRET_KEY environment variable. "
                "For now, using a temporary key (NOT SECURE FOR PRODUCTION).",
                UserWarning
            )
            # Use a fallback but warn - this should be fixed
            import secrets
            os.environ['SECRET_KEY'] = secrets.token_hex(32)
    
    return config_class

