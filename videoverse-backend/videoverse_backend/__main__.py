from videoverse_backend.settings import settings
from videoverse_backend.web.application import get_app
from videoverse_backend.web.granian_app import GranianApplication
from videoverse_backend.web.hypercorn_app import HypercornApplication


def main() -> None:
	"""Entrypoint of the application."""
	if settings.USE_HYPERCORN:
		app = get_app()
		hypercorn_app = HypercornApplication(app)
		hypercorn_app.run()
	else:
		GranianApplication.run()


if __name__ == "__main__":
	main()
