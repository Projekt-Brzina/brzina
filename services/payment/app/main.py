from fastapi import FastAPI
from .config import settings
from .db import get_pool, close_pool
from .kafka_consumer import start_consumer_loop
from .routers import payments
import structlog
import logging
from prometheus_fastapi_instrumentator import Instrumentator

def setup_logging():
	logging.basicConfig(format="%(message)s", stream=None, level=logging.INFO)
	structlog.configure(
		processors=[
			structlog.processors.JSONRenderer()
		],
		wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
		context_class=dict,
		logger_factory=structlog.stdlib.LoggerFactory(),
		cache_logger_on_first_use=True,
	)

def create_app():
	setup_logging()
	app = FastAPI(title=settings.service_name)
	app.include_router(payments.router)

	Instrumentator().instrument(app).expose(app)

	@app.on_event("startup")
	async def startup():
		await get_pool()
		start_consumer_loop()

	@app.on_event("shutdown")
	async def shutdown():
		await close_pool()

	return app

app = create_app()
