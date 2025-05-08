from fastapi import FastAPI, HTTPException, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.status import HTTP_401_UNAUTHORIZED

from videoverse_backend.core import SKIP_URLS


class StaticAPITokenMiddleware(BaseHTTPMiddleware):
	def __init__(self, app: FastAPI, api_tokens: list[str]) -> None:
		super().__init__(app)
		self.api_tokens = api_tokens

	async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
		if request.url.path in SKIP_URLS:
			return await call_next(request)

		authorization: str = request.headers.get("Authorization", "")
		if not authorization:
			raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Missing API Token")

		scheme, _, token = authorization.partition(" ")
		if scheme.lower() != "bearer":
			raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Invalid authentication scheme")

		if token not in self.api_tokens:
			raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Invalid API Token")

		return await call_next(request)
