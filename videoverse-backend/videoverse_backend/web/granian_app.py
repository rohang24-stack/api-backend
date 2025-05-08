from granian import Granian
from granian.constants import Interfaces

from videoverse_backend.settings import settings


class GranianApplication:
	"""
	Custom Granian application.

	This class is used to start Hypercorn with the FastAPI application.
	"""

	@staticmethod
	def run() -> None:
		"""
		Run the FastAPI application with Hypercorn.
		"""
		granian_app = Granian(
			target="videoverse_backend.web.application:videoverse_app",
			interface=Interfaces.ASGI,
			address=settings.HOST,
			port=settings.PORT,
			workers=settings.WORKERS_COUNT,
			reload=settings.DEBUG,
		)
		granian_app.serve()
