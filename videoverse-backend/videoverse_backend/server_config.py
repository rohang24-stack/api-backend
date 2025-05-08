from hypercorn import Config

from videoverse_backend.settings import settings


class HypercornConfig(Config):
	bind = [f"{settings.HOST}:{settings.PORT}"]
	workers = settings.WORKERS_COUNT
	use_reloader = settings.DEBUG
	accesslog = None
	errorlog = None
	loglevel = "CRITICAL" if settings.DEBUG else "DEBUG"
