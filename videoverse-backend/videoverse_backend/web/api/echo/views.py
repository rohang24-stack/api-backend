from fastapi import APIRouter

from videoverse_backend.core import DEFAULT_ROUTE_OPTIONS, CommonResponseSchema, StatusEnum
from videoverse_backend.web.api.echo.schema import Message

echo_router = APIRouter(prefix="/echo", tags=["Echo"])


@echo_router.post("", **DEFAULT_ROUTE_OPTIONS)
async def send_echo_message(
	incoming_message: Message,
) -> CommonResponseSchema:
	"""
	Sends echo back to user.

	:param incoming_message: incoming message.
	:returns: message same as the incoming.
	"""
	return CommonResponseSchema(
		status=StatusEnum.SUCCESS,
		message=incoming_message.message,
	)
