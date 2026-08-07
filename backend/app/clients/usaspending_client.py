from typing import Any
from urllib.parse import urlencode

import httpx

from app.config import get_settings


class USAspendingClient:
    def __init__(self, base_url: str | None = None, timeout: float = 20.0) -> None:
        settings = get_settings()
        self.base_url = str(base_url or settings.usaspending_base_url).rstrip("/")
        self.timeout = timeout

    def url_for(self, path: str, params: dict[str, Any] | None = None) -> str:
        url = f"{self.base_url}/{path.lstrip('/')}"
        if params:
            return f"{url}?{urlencode(params)}"
        return url

    async def get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(self.url_for(path), params=params)
            response.raise_for_status()
            return response.json()

    async def post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(self.url_for(path), json=payload)
            response.raise_for_status()
            return response.json()
