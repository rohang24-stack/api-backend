from fastapi import APIRouter, File, UploadFile

from videoverse_backend.core import DEFAULT_ROUTE_OPTIONS, APIResponse
from videoverse_backend.web.api.video.controller import VideoController
from videoverse_backend.web.api.video.schema import MergeSchema, ShareLinkSchema, TrimSchema

video_router = APIRouter(prefix="/video", tags=["Video"])


@video_router.post(
	"/upload",
	summary="Upload a video file with maximum size of 25MB",
	**DEFAULT_ROUTE_OPTIONS,
)
async def upload_video(file: UploadFile = File(...)) -> APIResponse:
	return await VideoController.upload_video(file)


@video_router.get(
	"/list",
	summary="List all videos",
	**DEFAULT_ROUTE_OPTIONS,
)
async def list_videos() -> APIResponse:
	return await VideoController.list_videos()


@video_router.post(
	"/trim",
	summary="Trim a video",
	**DEFAULT_ROUTE_OPTIONS,
)
async def trim_video(body: TrimSchema) -> APIResponse:
	return await VideoController.trim_video(body)


@video_router.post(
	"/merge",
	summary="Merge videos together",
	**DEFAULT_ROUTE_OPTIONS,
)
async def merge_videos(body: MergeSchema) -> APIResponse:
	return await VideoController.merge_videos(body)


@video_router.post(
	"/share",
	summary="Generate a shareable link for a video",
)
async def generate_share_link(body: ShareLinkSchema) -> APIResponse:
	return await VideoController.share_video(body)
