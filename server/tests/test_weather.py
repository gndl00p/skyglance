import json

import httpx
import pytest
import respx

from server.config import Settings
from server.upstreams import weather


@pytest.fixture
def settings(monkeypatch):
    monkeypatch.setenv("BADGE_TOKEN", "t")
    monkeypatch.setenv("METAR_STATION", "KLBB")
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
    payload = json.loads((fixtures_dir / "metar_klbb.json").read_text())

    with respx.mock(base_url="https://aviationweather.gov") as m:
        m.get("/api/data/metar").mock(return_value=httpx.Response(200, json=payload))

        async with httpx.AsyncClient() as client:
            result = await weather.get(client, settings)

    # 27°C = 80°F (rounded)
    assert result["temp_f"] == 81
    assert result["station"] == "KLBB"
    assert result["flight_category"] == "VFR"
    assert result["wind"] == "190 21kt G27"
    assert "BKN080" in result["summary"]
    assert result["ceiling_ft"] == 8000
    assert result["visibility_sm"] == 10.0
    assert result["stale"] is False


@pytest.mark.asyncio
async def test_weather_cached_within_ttl(settings, fixtures_dir):
    payload = json.loads((fixtures_dir / "metar_klbb.json").read_text())

    with respx.mock(base_url="https://aviationweather.gov") as m:
        route = m.get("/api/data/metar").mock(return_value=httpx.Response(200, json=payload))

        async with httpx.AsyncClient() as client:
            await weather.get(client, settings)
            await weather.get(client, settings)

    assert route.call_count == 1


@pytest.mark.asyncio
async def test_weather_stale_fallback_on_error(settings, fixtures_dir):
    payload = json.loads((fixtures_dir / "metar_klbb.json").read_text())

    with respx.mock(base_url="https://aviationweather.gov") as m:
        m.get("/api/data/metar").mock(return_value=httpx.Response(200, json=payload))
        async with httpx.AsyncClient() as client:
            await weather.get(client, settings)

    weather._cache._entry = (weather._cache._entry[0] - 1e6, weather._cache._entry[1])

    with respx.mock(base_url="https://aviationweather.gov") as m:
        m.get("/api/data/metar").mock(return_value=httpx.Response(500))
        async with httpx.AsyncClient() as client:
            result = await weather.get(client, settings)

    assert result["stale"] is True
    assert result["temp_f"] == 81


@pytest.mark.asyncio
async def test_weather_default_when_never_succeeded(settings):
    with respx.mock(base_url="https://aviationweather.gov") as m:
        m.get("/api/data/metar").mock(return_value=httpx.Response(500))
        async with httpx.AsyncClient() as client:
            result = await weather.get(client, settings)

    assert result["stale"] is True
    assert result["temp_f"] is None
    assert result["flight_category"] is None


@pytest.mark.asyncio
async def test_flight_category_classification(settings):
    # BKN at 700 ft with 2 SM vis → IFR
    payload = [{
        "icaoId": "KLBB",
        "temp": 10, "wdir": 360, "wspd": 5,
        "visib": "2", "rawOb": "",
        "clouds": [{"cover": "BKN", "base": 700}],
    }]
    with respx.mock(base_url="https://aviationweather.gov") as m:
        m.get("/api/data/metar").mock(return_value=httpx.Response(200, json=payload))
        async with httpx.AsyncClient() as client:
            result = await weather.get(client, settings)
    assert result["flight_category"] == "IFR"
    assert result["ceiling_ft"] == 700
    assert result["visibility_sm"] == 2.0


@pytest.mark.asyncio
async def test_flight_category_lifr(settings):
    # 300 ft ceiling + 0.5 SM vis → LIFR
    payload = [{
        "icaoId": "KLBB",
        "temp": 5, "wdir": 0, "wspd": 0,
        "visib": "1/2", "rawOb": "",
        "clouds": [{"cover": "OVC", "base": 300}],
    }]
    with respx.mock(base_url="https://aviationweather.gov") as m:
        m.get("/api/data/metar").mock(return_value=httpx.Response(200, json=payload))
        async with httpx.AsyncClient() as client:
            result = await weather.get(client, settings)
    assert result["flight_category"] == "LIFR"
    assert result["wind"] == "CALM"


@pytest.mark.asyncio
async def test_flight_category_mvfr(settings):
    # 2500 ft ceiling → MVFR
    payload = [{
        "icaoId": "KLBB",
        "temp": 18, "wdir": 240, "wspd": 10,
        "visib": "10", "rawOb": "",
        "clouds": [{"cover": "SCT", "base": 2000}, {"cover": "BKN", "base": 2500}],
    }]
    with respx.mock(base_url="https://aviationweather.gov") as m:
        m.get("/api/data/metar").mock(return_value=httpx.Response(200, json=payload))
        async with httpx.AsyncClient() as client:
            result = await weather.get(client, settings)
    assert result["flight_category"] == "MVFR"
    assert result["ceiling_ft"] == 2500
