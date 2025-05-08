import os
import tempfile
from datetime import timedelta
from typing import Any

import firebase_admin
from firebase_admin import credentials, storage


class FirebaseService:
	def __init__(self) -> None:
		cred = credentials.Certificate("creds.json")
		firebase_admin.initialize_app(
			cred,
			{
				"storageBucket": "videoverse-c744a.appspot.com",
			},
		)
		self.bucket = storage.bucket()

	def upload_file(self, file_name: str, file_path: Any) -> None:
		blob = self.bucket.blob(file_name)
		blob.upload_from_filename(file_path)

	def download_file(self, file_name: str, file_path: str, destination_dir: str | None = None) -> str:
		if destination_dir is not None:
			os.makedirs(destination_dir, exist_ok=True)

			temp_input_path = os.path.join(destination_dir, file_name)

			blob = self.bucket.blob(file_path)
			blob.download_to_filename(temp_input_path)

			return temp_input_path
		else:
			blob = self.bucket.blob(file_path)
			_, temp_input_path = tempfile.mkstemp(suffix=f".{file_name.split('.')[-1]}")
			blob.download_to_filename(temp_input_path)

			return temp_input_path

	def get_signed_url(self, file_name: str, expiration: timedelta) -> str:
		blob = self.bucket.blob(file_name)
		return blob.generate_signed_url(
			version="v4",
			expiration=expiration,
			method="GET",
		)


firebase_service = FirebaseService()
