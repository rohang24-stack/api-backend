import json
import os
import subprocess
from typing import Any

from videoverse_backend.settings import settings


class VideoService:
	@staticmethod
	def get_video_duration(file_path: Any) -> float:
		cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", file_path]
		result = subprocess.run(
			cmd,
			check=True,
			capture_output=settings.DEBUG,
		)
		output = json.loads(result.stdout)
		return float(output["format"]["duration"])

	@staticmethod
	def trim_video(file_path: str, start_time: float | None, end_time: float | None, output_path: str) -> None:
		command = ["ffmpeg", "-i", file_path, "-c", "copy"]

		if start_time is not None:
			command.extend(["-ss", str(start_time)])

		if end_time is not None:
			command.extend(["-to", str(end_time)])

		command.append(output_path)

		process = subprocess.Popen(
			command,
			stdout=subprocess.PIPE,
			stderr=subprocess.PIPE,
			universal_newlines=True,
			preexec_fn=os.setsid,
		)
		stdout, stderr = process.communicate()

	@staticmethod
	def merge_videos(list_file_path: str, output_path: str) -> None:
		command = [
			"ffmpeg",
			"-f",
			"concat",
			"-safe",
			"0",
			"-i",
			list_file_path,
			"-c",
			"copy",
			output_path,
		]
		subprocess.run(command, check=True)
