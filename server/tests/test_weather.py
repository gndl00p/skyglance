import json

import httpx
import pytest
import respx

from server.config import Settings
from server.upstreams import weather


@pytest.fixture
def settings(monkeypatch):
    monkeypatch.setenv("BADGE_TOKEN", "t")
    monkeypatch.setenv("WEATHER_LATITUDE", "30.27")
    monkeypatch.setenv("WEATHER_LONGITUDE", "-97.74")
    monkeypatch.setenv("GOOGLE_SERVICE_ACCOUNT_JSON", "/tmp/x")
    monkeypatch.setenv("GOOGLE_CALENDAR_ID", "x@example.com")
    monkeypatch.setenv("ZOHODESK_CLIENT_ID", "a")
    monkeypatch.setenv("ZOHODESK_CLIENT_SECRET", "b")
    monkeypatch.setenv("ZOHODESK_REFRESH_TOKEN", "c")
    monkeypatch.setenv("ZOHODESK_ORG_ID", "1")
    monkeypatch.setenv("ZOHOCRM_CLIENT_ID", "a")
    monkeypatch.setenv("ZOHOCRM_CLIENT_SECRET", "b")
    monkeypatch.setenv("ZOHOCRM_REFRESH_TOKEN", "c")
    monkeypatch.setenv("ZOHOCRM_USER_ID", "99")
    return Settings()


@pytest.fixture(autouse=True)
def reset_cache():
    weather._cache.__init__(ttl_seconds=weather._cache.ttl)


@pytest.mark.asyncio
async def test_weather_happy_path(settings, fixtures_dir):
    payload = json.loads((fixtures_dir / "open_meteo_sunny.json").read_text())

    with respx.mock(base_url="https://api.open-meteo.com") as m:
        m.get("/v1/forecast").mock(return_value=httpx.Response(200, json=payload))

        async with httpx.AsyncClient() as client:
            result = await weather.get(client, settings)

    assert result["temp_f"] == 72
    assert result["icon"] == "sun"
    assert "sunny" in result["summary"].lower() or "clear" in result["summary"].lower()
    assert result["stale"] is False


@pytest.mark.asyncio
async def test_weather_cached_within_ttl(settings, fixtures_dir):
    payload = json.loads((fixtures_dir / "open_meteo_sunny.json").read_text())

    with respx.mock(base_url="https://api.open-meteo.com") as m:
        route = m.get("/v1/forecast").mock(return_value=httpx.Response(200, json=payload))

        async with httpx.AsyncClient() as client:
            await weather.get(client, settings)
            await weather.get(client, settings)

    assert route.call_count == 1


@pytest.mark.asyncio
async def test_weather_stale_fallback_on_error(settings, fixtures_dir):
    payload = json.loads((fixtures_dir / "open_meteo_sunny.json").read_text())

    with respx.mock(base_url="https://api.open-meteo.com") as m:
        m.get("/v1/forecast").mock(return_value=httpx.Response(200, json=payload))
        async with httpx.AsyncClient() as client:
            await weather.get(client, settings)

    # Force cache miss by expiring TTL, then fail upstream.
    weather._cache._entry = (weather._cache._entry[0] - 1e6, weather._cache._entry[1])

    with respx.mock(base_url="https://api.open-meteo.com") as m:
        m.get("/v1/forecast").mock(return_value=httpx.Response(500))
        async with httpx.AsyncClient() as client:
            result = await weather.get(client, settings)

    assert result["stale"] is True
    assert result["temp_f"] == 72


@pytest.mark.asyncio
async def test_weather_default_when_never_succeeded(settings):
    with respx.mock(base_url="https://api.open-meteo.com") as m:
        m.get("/v1/forecast").mock(return_value=httpx.Response(500))
        async with httpx.AsyncClient() as client:
            result = await weather.get(client, settings)

    assert result["stale"] is True
    assert result["temp_f"] is None
    assert result["icon"] == "none"