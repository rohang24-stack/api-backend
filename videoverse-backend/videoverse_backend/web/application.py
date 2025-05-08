from importlib import metadata
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware

from videoverse_backend.core import DEFAULT_ROUTE_OPTIONS, TOKENS, CommonResponseSchema, StatusEnum, configure_logging
from videoverse_backend.middlewares import LoggingMiddleware, StaticAPITokenMiddleware
from videoverse_backend.web.api.router import api_router
from videoverse_backend.web.lifespan import lifespan

APP_ROOT = Path(__file__).parent.parent


def get_app() -> FastAPI:
	"""
	Get FastAPI application.

	This is the main constructor of an application.

	:return: application.
	"""
	app = FastAPI(
		title="Videoverse Backend",
		version=metadata.version("videoverse_backend"),
		lifespan=lifespan,
		docs_url=None,
		redoc_url=None,
		openapi_url="/api/openapi.json",
		default_response_class=ORJSONResponse,
	)

	app.add_middleware(
		CORSMiddleware,  # type: ignore
		allow_origins=["*"],
		allow_credentials=True,
		allow_methods=["*"],
		allow_headers=["*"],
	)

	app.add_middleware(
		StaticAPITokenMiddleware,  # type: ignore
		api_tokens=TOKENS,
	)  # type: ignore

	app.add_middleware(LoggingMiddleware)  # type: ignore

	app.include_router(router=api_router, prefix="/api")

	app.mount("/static", StaticFiles(directory=APP_ROOT / "static"), name="static")

	@app.get("/", tags=["Root"], **DEFAULT_ROUTE_OPTIONS)
	def read_root() -> CommonResponseSchema:
		return CommonResponseSchema(
			status=StatusEnum.SUCCESS,
			message="Welcome to Videoverse Fusion Backend!!",
			data={
				"ping": "pong",
			},
		)

	configure_logging()
	return app


videoverse_app = get_app()
