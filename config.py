import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'neuro-symptom-checker-secret-2024')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///illness.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024  # 2MB limit (low-bandwidth)
    
    # ML Model paths
    MODELS_DIR = os.path.join(os.path.dirname(__file__), 'app', 'ml', 'models')
    DATA_DIR = os.path.join(os.path.dirname(__file__), 'app', 'data')

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
