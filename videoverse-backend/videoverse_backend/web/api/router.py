from fastapi.routing import APIRouter

from videoverse_backend.web.api.docs import docs_router
from videoverse_backend.web.api.echo import echo_router
from videoverse_backend.web.api.monitoring import health_router
from videoverse_backend.web.api.video import video_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(docs_router)
api_router.include_router(echo_router)
api_router.include_router(video_router)
