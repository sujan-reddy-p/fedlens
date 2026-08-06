from typing import Any

import httpx

from app.config import get_settings


class USAspendingClient:
    def __init__(self, base_url: str | None = None, timeout: float = 20.0) -> None:
        settings = get_settings()
        self.base_url = str(base_url or settings.usaspending_base_url).rstrip("/")
        self.timeout = timeout

    async def post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        url = f"{self.base_url}/{path.lstrip('/')}"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            return response.json()
