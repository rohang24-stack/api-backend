from fastapi import APIRouter

from videoverse_backend.core import DEFAULT_ROUTE_OPTIONS, CommonResponseSchema, StatusEnum

router = APIRouter()

health_router = APIRouter(tags=["Monitoring", "Health"])


@health_router.get("/health", **DEFAULT_ROUTE_OPTIONS)
def health_check() -> CommonResponseSchema:
	"""
	Checks the health of a project.

	It returns 200 if the project is healthy.
	"""
	return CommonResponseSchema(
		status=StatusEnum.SUCCESS,
		message="The project is healthy.",
	)
