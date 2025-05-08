from enum import Enum

from pydantic import UUID4, BaseModel


class TrimType(str, Enum):
	START = "start"
	END = "end"


class TrimSchema(BaseModel):
	video_id: UUID4
	trim_time: float | None
	trim_type: TrimType
	save_as_new: bool | None = False


class MergeSchema(BaseModel):
	video_ids: list[UUID4]
	output_filename: str


class ShareLinkSchema(BaseModel):
	video_id: UUID4
	expiry_hours: float = 24.0
