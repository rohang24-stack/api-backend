import asyncio
import os
import subprocess
import tempfile as sync_tempfile
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

import aiofiles
from aiofiles import tempfile
from fastapi import UploadFile
from fastapi.encoders import jsonable_encoder
from pydantic import UUID4
from starlette import status

from videoverse_backend.core import APIResponse, StatusEnum, logger
from videoverse_backend.dao import VideoDAO
from videoverse_backend.db import VideoModel
from videoverse_backend.services import FileService, VideoService
from videoverse_backend.services.firebase_service import firebase_service
from videoverse_backend.settings import settings
from videoverse_backend.web.api.video.schema import MergeSchema, ShareLinkSchema, TrimSchema, TrimType


class VideoController:
	@staticmethod
	@contextmanager
	def manage_temp_file(suffix: str) -> Any:
		fd: int | None = None
		path: str | None = None
		try:
			fd, path = sync_tempfile.mkstemp(suffix=suffix)
			yield path
		finally:
			if fd:
				os.close(fd)
			if path and os.path.exists(path):
				os.unlink(path)

	@staticmethod
	async def upload_video(file: UploadFile) -> APIResponse:
		try:
			file_size = FileService.get_file_size(file)
			if file_size > settings.MAX_FILE_SIZE:
				return APIResponse(
					status_=StatusEnum.ERROR,
					message=f"File size must be less than {settings.MAX_FILE_SIZE}MB",
					status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
				)

			async with tempfile.NamedTemporaryFile(delete=False) as temp_file:
				await temp_file.write(await file.read())
				temp_file_path = temp_file.name

			duration = VideoService.get_video_duration(temp_file_path)
			if not (settings.MIN_DURATION <= duration <= settings.MAX_DURATION):
				logger.info(f"Removing video since its duration is {duration}")
				os.unlink(temp_file_path)  # type: ignore
				return APIResponse(
					status_=StatusEnum.ERROR,
					message=f"Video duration must be between {settings.MIN_DURATION} and {settings.MAX_DURATION} "
					f"seconds",
					status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
				)

			filename_without_extension, extension = os.path.splitext(file.filename)  # type: ignore
			firebase_path = f"videos/{filename_without_extension}_{uuid4()}{extension}"
			firebase_service.upload_file(firebase_path, temp_file_path)

			video = await VideoDAO().create(  # type: ignore
				{
					"filename": file.filename,
					"path": firebase_path,
					"duration": duration,
					"size": file_size,
				},
			)
			return APIResponse(
				status_=StatusEnum.SUCCESS,
				message="Video uploaded successfully",
				data={
					"id": video.id,
				},
				status_code=status.HTTP_201_CREATED,
			)
		except Exception as exception:
			logger.error(f"Error while uploading video: {exception}")
			return APIResponse(
				status_=StatusEnum.ERROR,
				message="Error while uploading video",
				data={"error": str(exception)},
				status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			)

	@staticmethod
	async def list_videos() -> APIResponse:
		try:
			videos = await VideoDAO().get_all()  # type: ignore
			return APIResponse(
				status_=StatusEnum.SUCCESS,
				message="List of videos",
				data=jsonable_encoder(videos),
			)
		except Exception as exception:
			logger.error(f"Error while listing videos: {exception}")
			return APIResponse(
				status_=StatusEnum.ERROR,
				message="Error while listing videos",
				data={"error": str(exception)},
				status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			)

	@staticmethod
	async def trim_video(body: TrimSchema) -> APIResponse:
		video: VideoModel = await VideoDAO().get(body.video_id)  # type: ignore
		if not video:
			return APIResponse(
				status_=StatusEnum.ERROR,
				message="The video you are trying to trim does not exist",
				status_code=status.HTTP_404_NOT_FOUND,
			)

		start_time, end_time = (
			(body.trim_time, video.duration) if body.trim_type == TrimType.START else (0, body.trim_time)
		)

		if not (0 < start_time < end_time):  # type: ignore
			return APIResponse(
				status_=StatusEnum.ERROR,
				message="Invalid trim value, start time must be greater than 0 and less than the video duration",
				status_code=status.HTTP_400_BAD_REQUEST,
			)

		temp_file_path = firebase_service.download_file(video.filename, video.path)
		with VideoController.manage_temp_file(suffix=f".{video.filename.split('.')[-1]}") as temp_output_path:
			try:
				os.unlink(temp_output_path)  # Remove the file created by manage_temp_file
				VideoService.trim_video(temp_file_path, start_time, end_time, temp_output_path)
				new_duration = end_time - start_time  # type: ignore
				new_size = os.path.getsize(temp_output_path) / (1024 * 1024)

				if body.save_as_new:
					file_name = video.filename.split(".")[0]
					extension = video.filename.split(".")[-1]
					trimmed_filename = f"{file_name}_trimmed_{uuid4()}.{extension}"
					firebase_path = f"videos/{trimmed_filename}"
					firebase_service.upload_file(firebase_path, temp_output_path)
					await VideoDAO().create(  # type: ignore
						{
							"filename": trimmed_filename,
							"path": firebase_path,
							"duration": new_duration,
							"size": new_size,
						},
					)

					return APIResponse(
						status_=StatusEnum.SUCCESS,
						message="Video trimmed and saved as a new copy successfully",
						status_code=status.HTTP_200_OK,
					)
				else:
					firebase_service.upload_file(video.path, temp_output_path)
					await VideoDAO().update(  # type: ignore
						video.id,
						{
							"duration": new_duration,
							"size": new_size,
						},
					)

					return APIResponse(
						status_=StatusEnum.SUCCESS,
						message="Video trimmed and updated successfully",
						status_code=status.HTTP_200_OK,
					)

			except subprocess.CalledProcessError as e:
				logger.error(f"Error during video trimming: {e}")
				return APIResponse(
					status_=StatusEnum.ERROR,
					message="Error while trimming video",
					status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
				)

	@staticmethod
	async def merge_videos(body: MergeSchema) -> APIResponse:
		if len(body.video_ids) < 2:
			return APIResponse(
				status_=StatusEnum.ERROR,
				message="At least two videos are required to merge",
				status_code=status.HTTP_400_BAD_REQUEST,
			)
		videos = await VideoController._fetch_videos(body.video_ids)
		if not videos:
			return APIResponse(
				status_=StatusEnum.ERROR,
				message="One or more videos do not exist",
				status_code=status.HTTP_404_NOT_FOUND,
			)

		async with aiofiles.tempfile.TemporaryDirectory() as temp_dir:
			try:
				input_files = await VideoController._download_videos(videos, temp_dir)

				output_filename, output_path = await VideoController._merge_videos_ffmpeg(
					input_files,
					body.output_filename,
					temp_dir,
				)

				new_video = await VideoController._upload_and_save_video(output_filename, output_path, videos)

				return APIResponse(
					status_=StatusEnum.SUCCESS,
					message="Videos merged successfully",
					status_code=status.HTTP_200_OK,
					data=jsonable_encoder(
						{
							"new_video_id": new_video.id,
							"filename": new_video.filename,
							"duration": new_video.duration,
							"size": new_video.size,
						},
					),
				)

			except Exception as exception:
				logger.error(f"Error while merging videos: {exception}")
				return APIResponse(
					status_=StatusEnum.ERROR,
					message="Error while merging videos",
					status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
					data={"error": str(exception)},
				)

	@staticmethod
	async def _fetch_videos(video_ids: list[UUID4]) -> list[VideoModel]:
		videos = []
		for video_id in video_ids:
			video = await VideoDAO().get(video_id)  # type: ignore
			if not video:
				logger.error(f"Video with id {video_id} does not exist")
				return []
			videos.append(video)
		return videos

	@staticmethod
	async def _download_videos(videos: list[VideoModel], temp_dir: str) -> list[str]:
		input_files = []
		download_tasks = []

		async def download_video(video: VideoModel):  # type: ignore # noqa
			unique_filename = f"{uuid4()}_{video.filename}"
			temp_file_path = firebase_service.download_file(unique_filename, video.path, temp_dir)
			if os.path.exists(temp_file_path):
				logger.info(f"Successfully downloaded: {temp_file_path}")
				return temp_file_path
			else:
				logger.error(f"Failed to download or access file: {temp_file_path}")
				raise FileNotFoundError(f"Failed to download or access file: {temp_file_path}")

		for video in videos:
			download_tasks.append(download_video(video))

		input_files = await asyncio.gather(*download_tasks)
		return input_files  # type: ignore

	@staticmethod
	async def _merge_videos_ffmpeg(input_files: list[str], output_filename: str, temp_dir: str) -> tuple[str, str]:
		list_file_path = os.path.join(temp_dir, "input_list.txt")
		async with aiofiles.open(list_file_path, "w") as list_file:
			for file_path in input_files:
				await list_file.write(f"file '{file_path}'\n")

		temp_output_filename = f"merged_{uuid4()}_{output_filename}"
		output_path = os.path.join(temp_dir, temp_output_filename)

		try:
			VideoService.merge_videos(list_file_path, output_path)
		except subprocess.CalledProcessError as e:
			logger.error(f"FFmpeg merge failed: {e.stderr}")
			raise

		return output_filename, output_path

	@staticmethod
	async def _upload_and_save_video(output_filename: str, output_path: str, videos: list[VideoModel]) -> VideoModel:
		filename = os.path.splitext(output_filename)[0]
		extension = os.path.splitext(output_filename)[-1]
		firebase_path = f"videos/{filename}_{uuid4()}{extension}"
		firebase_service.upload_file(firebase_path, output_path)

		new_duration = sum(video.duration for video in videos)
		new_size = os.path.getsize(output_path) / (1024 * 1024)

		new_video = await VideoDAO().create(  # type: ignore
			{
				"filename": output_filename,
				"path": firebase_path,
				"duration": new_duration,
				"size": new_size,
			},
		)

		return new_video

	@staticmethod
	async def share_video(body: ShareLinkSchema) -> APIResponse:
		video = await VideoDAO().get(body.video_id)  # type: ignore
		if not video:
			return APIResponse(
				status_=StatusEnum.ERROR,
				message="The video you are trying to share does not exist",
				status_code=status.HTTP_404_NOT_FOUND,
			)
		try:
			expiration = timedelta(hours=body.expiry_hours)
			signed_url = firebase_service.get_signed_url(video.path, expiration)

			expiry_time = datetime.now(UTC) + expiration

			return APIResponse(
				status_=StatusEnum.SUCCESS,
				message="Shareable link generated successfully",
				status_code=status.HTTP_200_OK,
				data=jsonable_encoder(
					{
						"share_link": signed_url,
						"expiry_time": expiry_time.isoformat(),
						"video_id": video.id,
						"video_name": video.filename,
					},
				),
			)

		except Exception as e:
			return APIResponse(
				status_=StatusEnum.ERROR,
				message=f"Error generating shareable link: {str(e)}",
				status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			)
