from typing import Type, TypedDict

from pydantic import BaseModel

from videoverse_backend.core.schema.common_response_schema import CommonResponseSchema


class RouteOptions(TypedDict):
	response_model_exclude_none: bool
	response_model: Type[BaseModel]


DEFAULT_ROUTE_OPTIONS: RouteOptions = {
	"response_model_exclude_none": True,
	"response_model": CommonResponseSchema,
}

SKIP_URLS = [
	"/",
	"/api/health",
	"/api/openapi.json",
	"/api/docs",
	"/api/redoc",
	"/api/auth",
	"/api/auth/login",
	"/static/docs/swagger-ui-bundle.js",
	"/static/docs/swagger-ui.css",
]

TOKENS = [
	"a3f8b00a7f21d0d8f9f6f3d52cfe1a90f7d36d8e8a3e4c5b1d1d5f3d9c9e3e1f",
]
