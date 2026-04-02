import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent


class BaseConfig:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{BASE_DIR / 'reconai.db'}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JSON_SORT_KEYS = False

    FERNET_KEY = os.getenv("FERNET_KEY", "")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
    OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
    OLLAMA_CHAT_MODEL = os.getenv("OLLAMA_CHAT_MODEL", "llama3.1:8b")
    MAX_ROWS_PER_TABLE = int(os.getenv("MAX_ROWS_PER_TABLE", 100_000))
    SENTRY_DSN = os.getenv("SENTRY_DSN", "")


class DevelopmentConfig(BaseConfig):
    DEBUG = True


class ProductionConfig(BaseConfig):
    DEBUG = False


def get_config():
    env = os.getenv("FLASK_ENV", "development").lower()
    return ProductionConfig if env == "production" else DevelopmentConfig
