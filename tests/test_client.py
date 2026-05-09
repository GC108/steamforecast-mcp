"""Tests for the steamforecast.app HTTP client (respx-mocked)."""
from __future__ import annotations

import httpx
import pytest
import respx

from steamforecast_mcp.client import SteamforecastClient


HADES_FORECAST = {
    "appid": 1145360,
    "name": "Hades",
    "genres": ["Action", "Indie", "RPG"],
    "model_version": "boxleiter_v1_1_2026_05_05",
    "p10_revenue_cents": 5_000_000,
    "p50_revenue_cents": 25_000_000,
    "p90_revenue_cents": 100_000_000,
    "methodology_url": "https://steamforecast.app/methodology",
}


@respx.mock
async def test_get_forecast_basic():
    respx.get("https://steamforecast.app/api/forecast").mock(
        return_value=httpx.Response(200, json=HADES_FORECAST)
    )
    c = SteamforecastClient()
    result = await c.get_forecast(1145360)
    assert result["appid"] == 1145360
    assert result["name"] == "Hades"
    assert result["p50_revenue_cents"] == 25_000_000


@respx.mock
async def test_get_forecast_with_overrides():
    route = respx.get("https://steamforecast.app/api/forecast").mock(
        return_value=httpx.Response(200, json=HADES_FORECAST)
    )
    c = SteamforecastClient()
    await c.get_forecast(1145360, wishlist=50_000, followers=10_000)
    assert route.called
    request = route.calls.last.request
    assert "wishlist=50000" in str(request.url)
    assert "followers=10000" in str(request.url)


@respx.mock
async def test_get_forecast_404_raises():
    respx.get("https://steamforecast.app/api/forecast").mock(
        return_value=httpx.Response(404, json={"detail": "appid 99999 not in catalog"})
    )
    c = SteamforecastClient()
    with pytest.raises(httpx.HTTPStatusError):
        await c.get_forecast(99999)


@respx.mock
async def test_get_comps_passes_k():
    respx.get("https://steamforecast.app/comps").mock(
        return_value=httpx.Response(200, json={"appid": 1145360, "comps": []})
    )
    c = SteamforecastClient()
    await c.get_comps(1145360, k=3)
    request = respx.calls.last.request
    assert "k=3" in str(request.url)


@respx.mock
async def test_get_llms_txt():
    respx.get("https://steamforecast.app/llms.txt").mock(
        return_value=httpx.Response(200, text="# Steam Launch Forecaster\n\n> Calibrated...")
    )
    c = SteamforecastClient()
    text = await c.get_llms_txt()
    assert text.startswith("# Steam Launch Forecaster")
