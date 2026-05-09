"""HTTP client for the steamforecast.app public API.

Wraps three public endpoints:
  - GET /api/forecast?appid=N   → calibrated P10/P50/P90 cone (JSON)
  - GET /comps?appid=N&k=K       → top-K nearest-neighbor comp games
  - GET /llms.txt                → AI-crawler discovery / methodology summary

The base URL is overridable via env var STEAMFORECAST_BASE_URL (useful for
local development / staging). Default is https://steamforecast.app.
"""
from __future__ import annotations

import os
from typing import Any

import httpx

DEFAULT_BASE_URL = os.environ.get("STEAMFORECAST_BASE_URL", "https://steamforecast.app")
USER_AGENT = "steamforecast-mcp/0.1 (+https://github.com/GC108/steamforecast-mcp)"
DEFAULT_TIMEOUT = 30.0


class SteamforecastClient:
    """Thin async wrapper over the public steamforecast.app API."""

    def __init__(
        self,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        user_agent: str = USER_AGENT,
    ):
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._user_agent = user_agent

    async def get_forecast(
        self,
        appid: int,
        *,
        wishlist: int | None = None,
        followers: int | None = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"appid": appid}
        if wishlist is not None:
            params["wishlist"] = wishlist
        if followers is not None:
            params["followers"] = followers
        async with httpx.AsyncClient(
            headers={"User-Agent": self._user_agent}, timeout=self._timeout
        ) as c:
            r = await c.get(f"{self._base_url}/api/forecast", params=params)
            r.raise_for_status()
            return r.json()

    async def get_comps(self, appid: int, k: int = 5) -> dict[str, Any]:
        async with httpx.AsyncClient(
            headers={"User-Agent": self._user_agent}, timeout=self._timeout
        ) as c:
            r = await c.get(f"{self._base_url}/comps", params={"appid": appid, "k": k})
            r.raise_for_status()
            return r.json()

    async def get_llms_txt(self) -> str:
        async with httpx.AsyncClient(
            headers={"User-Agent": self._user_agent}, timeout=self._timeout
        ) as c:
            r = await c.get(f"{self._base_url}/llms.txt")
            r.raise_for_status()
            return r.text
