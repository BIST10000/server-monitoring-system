from __future__ import annotations

from fastapi import Header, HTTPException, status

from app.settings import settings


def require_api_key(x_api_key: str | None = Header(default=None, alias="X-Api-Key")) -> str:
    if x_api_key is None or x_api_key not in settings.api_key_set:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
    return x_api_key

