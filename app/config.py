import os
from datetime import timedelta


class BaseConfig:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-change-me')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///neon_roo_computers.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    COMPANY_NAME = os.getenv('COMPANY_NAME', 'Neon Roo Computers & Upgrades')
    BASE_URL = os.getenv('BASE_URL', 'http://127.0.0.1:5000').rstrip('/')
    STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY', '')
    STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET', '')
    STRIPE_PUBLIC_KEY = os.getenv('STRIPE_PUBLIC_KEY', '')
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 8 * 1024 * 1024))
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = os.getenv('SESSION_COOKIE_SAMESITE', 'Lax')
    PERMANENT_SESSION_LIFETIME = timedelta(days=int(os.getenv('SESSION_LIFETIME_DAYS', '14')))
    PREFERRED_URL_SCHEME = os.getenv('PREFERRED_URL_SCHEME', 'https')


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    ENV_NAME = 'development'


class ProductionConfig(BaseConfig):
    DEBUG = False
    ENV_NAME = 'production'
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True


CONFIG_MAP = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
}
