from __future__ import annotations

import logging

from fastapi import FastAPI
from pythonjsonlogger import jsonlogger

from app.api import router as api_router
from app.settings import settings
from app.ui import router as ui_router


def _configure_logging() -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(jsonlogger.JsonFormatter("%(levelname)s %(name)s %(message)s"))
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(settings.log_level.upper())


_configure_logging()

app = FastAPI(title=settings.project_name, root_path=settings.api_root_path)
app.include_router(api_router)
if settings.ui_enabled:
    app.include_router(ui_router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}

