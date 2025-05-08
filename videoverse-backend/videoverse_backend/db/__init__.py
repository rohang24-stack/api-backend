from functools import wraps
from typing import Any, AsyncGenerator, Awaitable, Callable, TypeVar, cast

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from videoverse_backend.db.models.video_model import VideoModel
from videoverse_backend.settings import settings

F = TypeVar("F", bound=Callable[..., Awaitable[Any]])


class Database:
	def __init__(self) -> None:
		self.engine = create_async_engine(
			settings.DATABASE_URL,
			echo=settings.DEBUG,
			future=True,
		)
		self.session_factory = async_sessionmaker(
			bind=self.engine,
			expire_on_commit=False,
			autocommit=False,
			autoflush=False,
			class_=AsyncSession,
		)

	async def get_db(self) -> AsyncGenerator[AsyncSession, None]:
		async with self.session_factory() as session:
			try:
				yield session
				await session.commit()
			except Exception:
				await session.rollback()
				raise


database = Database()


def inject_session(func: F) -> F:
	@wraps(func)
	async def wrapper(*args: Any, **kwargs: Any) -> Any:
		async for session in database.get_db():
			if "session" in kwargs:
				raise ValueError("Session argument already provided")
			kwargs["session"] = session
			return await func(*args, **kwargs)

	return cast(F, wrapper)


__all__ = [
	"database",
	"inject_session",
	"VideoModel",
]
