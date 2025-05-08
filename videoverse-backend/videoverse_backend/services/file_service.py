from fastapi import UploadFile


class FileService:
	@staticmethod
	def get_file_size(file: UploadFile) -> float:
		file.file.seek(0, 2)
		file_size = file.file.tell() / (1024 * 1024)
		file.file.seek(0)
		return file_size
