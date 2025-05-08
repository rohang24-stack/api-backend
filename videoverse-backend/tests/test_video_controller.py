import json
import os
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import UploadFile
from videoverse_backend.core import StatusEnum
from videoverse_backend.web.api.video.controller import VideoController
from videoverse_backend.web.api.video.schema import MergeSchema, ShareLinkSchema, TrimSchema, TrimType


@pytest.fixture
def video_controller():
	return VideoController()


@pytest.mark.asyncio
async def test_upload_video_success(video_controller):
	mock_file = AsyncMock(spec=UploadFile)
	mock_file.filename = "test_video.mp4"
	mock_file.read.return_value = b"fake video content"

	video_id = str(uuid.uuid4())

	with (
		patch("videoverse_backend.web.api.video.controller.FileService.get_file_size", return_value=5),
		patch("videoverse_backend.web.api.video.controller.VideoService.get_video_duration", return_value=30),
		patch("videoverse_backend.web.api.video.controller.firebase_service.upload_file"),
		patch("videoverse_backend.web.api.video.controller.VideoDAO.create") as mock_create,
	):
		mock_create.return_value = MagicMock(id=video_id)
		response = await video_controller.upload_video(mock_file)
	assert response.status_code == 201
	res = json.loads(response.body.decode("utf-8"))
	assert res.get("status") == StatusEnum.SUCCESS
	assert res.get("data").get("id") == video_id


@pytest.mark.asyncio
async def test_upload_video_file_too_large(video_controller):
	mock_file = AsyncMock(spec=UploadFile)
	mock_file.filename = "large_video.mp4"

	with patch("videoverse_backend.web.api.video.controller.FileService.get_file_size", return_value=1000):
		response = await video_controller.upload_video(mock_file)

	res = json.loads(response.body.decode("utf-8"))
	assert res.get("status") == StatusEnum.ERROR
	assert response.status_code == 413


@pytest.mark.asyncio
async def test_list_videos_success(video_controller):
	mock_videos = [MagicMock(id="1", filename="video1.mp4"), MagicMock(id="2", filename="video2.mp4")]

	with patch("videoverse_backend.web.api.video.controller.VideoDAO.get_all", return_value=mock_videos):
		response = await video_controller.list_videos()

	res = json.loads(response.body.decode("utf-8"))
	assert res.get("status") == StatusEnum.SUCCESS
	assert len(res.get("data")) == 2


@pytest.mark.asyncio
async def test_trim_video_success(video_controller):
	video_id = str(uuid.uuid4())
	mock_video = MagicMock(id=video_id, filename="video.mp4", duration=60, path="path/to/video.mp4")
	trim_schema = TrimSchema(video_id=video_id, trim_type=TrimType.START, trim_time=10, save_as_new=False)

	mock_input_path = "/tmp/mock_input.mp4"

	with (
		patch("videoverse_backend.web.api.video.controller.VideoDAO.get", return_value=mock_video),
		patch(
			"videoverse_backend.web.api.video.controller.firebase_service.download_file",
			return_value=mock_input_path,
		),
		patch("videoverse_backend.web.api.video.controller.VideoService.trim_video") as mock_trim,
		patch("videoverse_backend.web.api.video.controller.firebase_service.upload_file"),
		patch("videoverse_backend.web.api.video.controller.VideoDAO.update"),
		patch("os.unlink"),
		patch("os.path.exists", return_value=True),
		patch("os.path.getsize", return_value=1000000),
	):
		response = await video_controller.trim_video(trim_schema)

		res = json.loads(response.body)
		assert res.get("status") == StatusEnum.SUCCESS.value
		assert response.status_code == 200

		mock_trim.assert_called_once()
		args, _ = mock_trim.call_args
		assert args[0] == mock_input_path
		assert abs(args[1] - 10.0) < 1e-6
		assert args[2] == 60
		valid_path_prefixes = ["/var/folders/", "/tmp/"]
		assert any(args[3].startswith(prefix) for prefix in valid_path_prefixes)
		mock_trim.assert_called_once()


@pytest.mark.asyncio
async def test_merge_videos_success(video_controller):
	video_id1, video_id2 = str(uuid.uuid4()), str(uuid.uuid4())
	mock_videos = [
		MagicMock(id=video_id1, filename="video1.mp4", duration=30),
		MagicMock(id=video_id2, filename="video2.mp4", duration=40),
	]
	merge_schema = MergeSchema(video_ids=[video_id1, video_id2], output_filename="merged.mp4")

	new_video_id = str(uuid.uuid4())
	mock_temp_dir = "/tmp/mock_temp_dir"
	mock_output_path = os.path.join(mock_temp_dir, f"merged_{new_video_id}_merged.mp4")

	async def mock_download_videos(videos, temp_dir):
		return [os.path.join(temp_dir, video.filename) for video in videos]

	mock_file = AsyncMock()
	mock_file.__aenter__.return_value = mock_file
	mock_file.write = AsyncMock()

	mock_named_temp_file = MagicMock()
	mock_named_temp_file.__enter__.return_value.name = mock_output_path

	with (
		patch("videoverse_backend.web.api.video.controller.VideoDAO.get", side_effect=mock_videos),
		patch("videoverse_backend.web.api.video.controller.aiofiles.tempfile.TemporaryDirectory") as mock_temp_dir_ctx,
		patch.object(VideoController, "_download_videos", new=mock_download_videos),
		patch("videoverse_backend.web.api.video.controller.VideoService.merge_videos") as mock_merge,
		patch("videoverse_backend.web.api.video.controller.firebase_service.upload_file"),
		patch("videoverse_backend.web.api.video.controller.VideoDAO.create") as mock_create,
		patch("os.path.exists", return_value=True),
		patch("os.path.getsize", return_value=1000000),
		patch("aiofiles.open", return_value=mock_file),
		patch("tempfile.NamedTemporaryFile", return_value=mock_named_temp_file),
	):
		mock_temp_dir_ctx.return_value.__aenter__.return_value = mock_temp_dir

		mock_merge.return_value = mock_output_path
		mock_create.return_value = MagicMock(id=new_video_id, filename="merged.mp4", duration=70, size=10)

		response = await video_controller.merge_videos(merge_schema)

	res = json.loads(response.body)
	assert res.get("status") == StatusEnum.SUCCESS.value
	assert response.status_code == 200
	assert res.get("data").get("new_video_id") == new_video_id

	mock_merge.assert_called_once()
	mock_create.assert_called_once()
	mock_file.write.assert_called()


@pytest.mark.asyncio
async def test_share_video_success(video_controller):
	video_id = str(uuid.uuid4())
	mock_video = MagicMock(id=video_id, filename="video.mp4", path="path/to/video.mp4")
	share_schema = ShareLinkSchema(video_id=video_id, expiry_hours=24)

	with (
		patch("videoverse_backend.web.api.video.controller.VideoDAO.get", return_value=mock_video),
		patch(
			"videoverse_backend.web.api.video.controller.firebase_service.get_signed_url",
			return_value="https://signed-url.com",
		),
	):
		response = await video_controller.share_video(share_schema)
	res = json.loads(response.body)
	assert res.get("status") == StatusEnum.SUCCESS
	assert response.status_code == 200
	assert "share_link" in res.get("data")


@pytest.mark.asyncio
async def test_upload_video_invalid_duration(video_controller):
	mock_file = AsyncMock(spec=UploadFile)
	mock_file.filename = "short_video.mp4"
	mock_file.read.return_value = b"fake video content"

	with (
		patch("videoverse_backend.web.api.video.controller.FileService.get_file_size", return_value=5),
		patch("videoverse_backend.web.api.video.controller.VideoService.get_video_duration", return_value=1),
	):
		response = await video_controller.upload_video(mock_file)

	res = json.loads(response.body)
	assert res.get("status") == StatusEnum.ERROR.value
	assert response.status_code == 422
	assert "Video duration must be between" in res.get("message")


@pytest.mark.asyncio
async def test_trim_video_not_found(video_controller):
	video_id = str(uuid.uuid4())
	trim_schema = TrimSchema(video_id=video_id, trim_type=TrimType.START, trim_time=10, save_as_new=False)

	with patch("videoverse_backend.web.api.video.controller.VideoDAO.get", return_value=None):
		response = await video_controller.trim_video(trim_schema)

	res = json.loads(response.body)
	assert res.get("status") == StatusEnum.ERROR.value
	assert response.status_code == 404
	assert "video you are trying to trim does not exist" in res.get("message")


@pytest.mark.asyncio
async def test_trim_video_invalid_trim_time(video_controller):
	video_id = str(uuid.uuid4())
	mock_video = MagicMock(id=video_id, filename="video.mp4", duration=60, path="path/to/video.mp4")
	trim_schema = TrimSchema(video_id=video_id, trim_type=TrimType.START, trim_time=70, save_as_new=False)

	with patch("videoverse_backend.web.api.video.controller.VideoDAO.get", return_value=mock_video):
		response = await video_controller.trim_video(trim_schema)

	res = json.loads(response.body)
	assert res.get("status") == StatusEnum.ERROR.value
	assert response.status_code == 400
	assert "Invalid trim value" in res.get("message")


@pytest.mark.asyncio
async def test_merge_videos_not_enough_videos(video_controller):
	merge_schema = MergeSchema(video_ids=[str(uuid.uuid4())], output_filename="merged.mp4")

	response = await video_controller.merge_videos(merge_schema)

	res = json.loads(response.body)
	assert res.get("status") == StatusEnum.ERROR.value
	assert response.status_code == 400
	assert "At least two videos are required to merge" in res.get("message")


@pytest.mark.asyncio
async def test_merge_videos_one_video_not_found(video_controller):
	video_id1, video_id2 = str(uuid.uuid4()), str(uuid.uuid4())
	merge_schema = MergeSchema(video_ids=[video_id1, video_id2], output_filename="merged.mp4")

	with patch("videoverse_backend.web.api.video.controller.VideoDAO.get", side_effect=[MagicMock(), None]):
		response = await video_controller.merge_videos(merge_schema)

	res = json.loads(response.body)
	assert res.get("status") == StatusEnum.ERROR.value
	assert response.status_code == 404
	assert "One or more videos do not exist" in res.get("message")


@pytest.mark.asyncio
async def test_share_video_not_found(video_controller):
	video_id = str(uuid.uuid4())
	share_schema = ShareLinkSchema(video_id=video_id, expiry_hours=24)

	with patch("videoverse_backend.web.api.video.controller.VideoDAO.get", return_value=None):
		response = await video_controller.share_video(share_schema)

	res = json.loads(response.body)
	assert res.get("status") == StatusEnum.ERROR.value
	assert response.status_code == 404
	assert "video you are trying to share does not exist" in res.get("message")


@pytest.mark.asyncio
async def test_share_video_firebase_error(video_controller):
	video_id = str(uuid.uuid4())
	mock_video = MagicMock(id=video_id, filename="video.mp4", path="path/to/video.mp4")
	share_schema = ShareLinkSchema(video_id=video_id, expiry_hours=24)

	with (
		patch("videoverse_backend.web.api.video.controller.VideoDAO.get", return_value=mock_video),
		patch(
			"videoverse_backend.web.api.video.controller.firebase_service.get_signed_url",
			side_effect=Exception("Firebase error"),
		),
	):
		response = await video_controller.share_video(share_schema)

	res = json.loads(response.body)
	assert res.get("status") == StatusEnum.ERROR.value
	assert response.status_code == 500
	assert "Error generating shareable link" in res.get("message")
