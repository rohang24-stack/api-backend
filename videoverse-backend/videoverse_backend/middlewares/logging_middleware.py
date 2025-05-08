from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from videoverse_backend.core import end_stage_logger, stage_logger


class LoggingMiddleware(BaseHTTPMiddleware):
	async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore
		if request.client:
			stage_logger.info(
				f'{request.client.host}:{request.client.port} - "{request.method} {request.url.path} '
				f'{request.scope['http_version']}"',
			)
		response = await call_next(request)
		if request.client:
			end_stage_logger.info(
				f'{request.client.host}:{request.client.port} - "{request.method} {request.url.path} '
				f'{request.scope['http_version']}" {response.status_code}',
			)
		return response
