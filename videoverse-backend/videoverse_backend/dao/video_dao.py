from videoverse_backend.dao.base_dao import BaseDAO
from videoverse_backend.db import VideoModel


class VideoDAO(BaseDAO[VideoModel]):
	def __init__(self) -> None:
		super().__init__(VideoModel)
