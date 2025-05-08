from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict
from starlette import status
from starlette.responses import JSONResponse

from videoverse_backend.core.utils.enums import StatusEnum


class CommonResponseSchema(BaseModel):
	status: StatusEnum
	message: str
	data: dict[Any, Any] | list[dict[Any, Any]] | None = None
	model_config = ConfigDict(
		json_encoders={
			datetime: lambda v: v.isoformat(),
		},
		extra="ignore",
		json_schema_extra={
			"example": {
				"status": "success",
				"message": "The project is healthy.",
			},
		},
	)


class APIResponse(JSONResponse):
	def __init__(
		self,
		status_: StatusEnum,
		message: str,
		data: dict[str, Any] | list[dict[str, Any]] | None = None,
		status_code: int = status.HTTP_200_OK,
	):
		content = CommonResponseSchema(status=status_, message=message, data=data).model_dump(exclude_none=True)
		super().__init__(content=content, status_code=status_code)
