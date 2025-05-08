from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

from videoverse_backend.db import database
from videoverse_backend.db.models.base import BaseModel


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
	app.middleware_stack = None
	app.middleware_stack = app.build_middleware_stack()
	async with database.engine.begin() as conn:
		await conn.run_sync(BaseModel.metadata.create_all)
	yield
