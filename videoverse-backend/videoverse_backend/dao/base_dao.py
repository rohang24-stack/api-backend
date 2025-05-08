# app/dao/base.py
from typing import Any, Generic, Sequence, Type, TypeVar

from sqlalchemy import Uuid, delete, select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from videoverse_backend.db import inject_session

T = TypeVar("T")


class BaseDAO(Generic[T]):
	def __init__(self, model: Type[T]):
		self.model = model

	@inject_session
	async def create(self, obj_in: dict[Any, Any], session: AsyncSession) -> T:
		try:
			db_obj = self.model(**obj_in)
			session.add(db_obj)
			await session.commit()
			await session.refresh(db_obj)
			return db_obj
		except SQLAlchemyError as exception:
			await session.rollback()
			raise exception

	@inject_session
	async def get(self, unique_id: int | Uuid, session: AsyncSession) -> T | None:  # type: ignore
		try:
			statement = select(self.model).where(self.model.id == unique_id)  # type: ignore
			result = await session.execute(statement)
			return result.scalars().first()
		except SQLAlchemyError as exception:
			raise exception

	@inject_session
	async def get_all(self, session: AsyncSession) -> Sequence[T]:
		try:
			statement = select(self.model)
			result = await session.execute(statement)
			return result.scalars().all()
		except SQLAlchemyError as exception:
			raise exception

	@inject_session
	async def update(
		self,
		unique_id: int | Uuid,  # type: ignore
		obj_in: dict[Any, Any],
		session: AsyncSession,
	) -> T | None:
		try:
			statement = (
				update(self.model)
				.where(self.model.id == unique_id)  # type: ignore
				.values(**obj_in)
				.returning(
					self.model,
				)
			)
			result = await session.execute(statement)
			await session.commit()
			return result.scalars().first()
		except SQLAlchemyError as exception:
			await session.rollback()
			raise exception

	@inject_session
	async def delete(self, unique_id: int, session: AsyncSession) -> bool:
		try:
			statement = delete(self.model).where(self.model.id == unique_id)  # type: ignore
			result = await session.execute(statement)
			await session.commit()
			return result.rowcount > 0  # noqa
		except SQLAlchemyError as exception:
			await session.rollback()
			raise exception
