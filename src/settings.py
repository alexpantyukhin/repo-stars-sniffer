"""Settings for the app"""
import os

TELEGRAM_API_TOKEN = os.getenv("TELEGRAM_API_TOKEN")
REDIS_HOST = os.getenv("REDIS_HOST") or 'localhost'
REDIS_PORT = os.getenv("REDIS_PORT") or '6379'

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL") or 'localhost'
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND") or 'localhost'

POSTGRESQL_USER = os.getenv('POSTGRESQL_USER') or 'user'
POSTGRESQL_PASSWORD = os.getenv('POSTGRESQL_PASSWORD') or 'password'
POSTGRESQL_HOST = os.getenv('POSTGRESQL_HOST') or 'localhost'
POSTGRESQL_PORT = os.getenv('POSTGRESQL_PORT') or '5432'
POSTGRESQL_DB = os.getenv('POSTGRESQL_DB') or 'db'

SECONDS_UPDATE = os.getenv('SECONDS_UPDATE') or 10 * 60
