import enum
import os
from functools import lru_cache
from typing import Any

from dotenv import load_dotenv


class LogLevel(str, enum.Enum):
	"""Possible log levels."""

	NOTSET = "NOTSET"
	DEBUG = "DEBUG"
	INFO = "INFO"
	WARNING = "WARNING"
	ERROR = "ERROR"
	FATAL = "FATAL"


class Environment(str, enum.Enum):
	"""Possible environments."""

	DEV = "DEV"
	PROD = "PROD"
	TEST = "TEST"


class Settings:
	"""
	Application settings.

	These parameters can be configured
	with environment variables.
	"""

	def __init__(self) -> None:
		load_dotenv(".env")

		self.HOST: str = os.getenv("HOST", "0.0.0.0")
		self.PORT: int = int(os.getenv("PORT", 8000))
		self.WORKERS_COUNT: int = int(os.getenv("WORKERS_COUNT", 1))
		self.DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"

		self.ENVIRONMENT: Environment = Environment[os.getenv("ENVIRONMENT", "DEV")]

		self.LOG_LEVEL: LogLevel = LogLevel.INFO

		self.DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./videoverse.db")

		self.USE_HYPERCORN: bool = os.getenv("USE_HYPERCORN", "False").lower() == "true"

		self.MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 25))
		self.MIN_DURATION = int(os.getenv("MIN_DURATION", 5))
		self.MAX_DURATION = int(os.getenv("MAX_DURATION", 300))
		self.EXPIRATION_TIME = int(os.getenv("EXPIRATION_TIME", 60))

	def __getitem__(self, key: str) -> Any:
		return getattr(self, key)


@lru_cache
def get_settings() -> Settings:
	"""Get application settings."""
	return Settings()


settings = Settings()
