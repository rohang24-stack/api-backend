import asyncio

from fastapi import FastAPI
from hypercorn.asyncio import serve
from loguru import logger

from videoverse_backend.server_config import HypercornConfig


class HypercornApplication:
	"""
	Custom Hypercorn application.

	This class is used to start Hypercorn with the FastAPI application.
	"""

	def __init__(
		self,
		app: FastAPI,
	) -> None:
		self.app = app

	def run(self) -> None:
		"""
		Run the FastAPI application with Hypercorn.
		"""
		config = HypercornConfig()
		logger.info("Configuring Hypercorn Server...")
		logger.info(f"Starting Hypercorn Server on http://{config.bind[0]}")  # noqa
		asyncio.run(serve(self.app, config))  # type: ignore
