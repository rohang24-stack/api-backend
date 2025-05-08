from uuid import uuid4

from sqlalchemy import Float, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from videoverse_backend.db.models.base import BaseModel


class VideoModel(BaseModel):
	__tablename__ = "video"

	id: Mapped[Uuid] = mapped_column(Uuid, primary_key=True, default=uuid4())  # type: ignore
	duration: Mapped[float] = mapped_column(Float, nullable=False)
	path: Mapped[str] = mapped_column(String, nullable=False)
	filename: Mapped[str] = mapped_column(String)
	size: Mapped[float] = mapped_column(Float)
