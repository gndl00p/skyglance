import httpx

from server.cache import TTLCache
from server.config import Settings

_cache = TTLCache(ttl_seconds=60)

_WMO = {
    0: ("clear", "sun"),
    1: ("sunny", "sun"),
    2: ("partly cloudy", "cloud"),
    3: ("cloudy", "cloud"),
    45: ("fog", "fog"),
    48: ("fog", "fog"),
    51: ("drizzle", "rain"),
    53: ("drizzle", "rain"),
    55: ("drizzle", "rain"),
    61: ("rain", "rain"),
    63: ("rain", "rain"),
    65: ("heavy rain", "rain"),
    66: ("freezing rain", "rain"),
    67: ("freezing rain", "rain"),
    71: ("snow", "snow"),
    73: ("snow", "snow"),
    75: ("heavy snow", "snow"),
    77: ("snow grains", "snow"),
    80: ("showers", "rain"),
    81: ("showers", "rain"),
    82: ("heavy showers", "rain"),
    85: ("snow showers", "snow"),
    86: ("snow showers", "snow"),
    95: ("thunderstorm", "storm"),
    96: ("thunderstorm", "storm"),
    99: ("thunderstorm", "storm"),
}


def _parse(payload: dict) -> dict:
    cur = payload["current"]
    code = int(cur["weather_code"])
    summary, icon = _WMO.get(code, ("unknown", "none"))
    return {
        "temp_f": int(round(float(cur["temperature_2m"]))),
        "summary": summary,
        "icon": icon,
        "stale": False,
    }


async def _fetch(client: httpx.AsyncClient, settings: Settings) -> dict:
    r = await client.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": settings.weather_latitude,
            "longitude": settings.weather_longitude,
            "current": "temperature_2m,weather_code",
            "temperature_unit": "fahrenheit",
        },
        timeout=2.0,
    )
    r.raise_for_status()
    return _parse(r.json())


async def get(client: httpx.AsyncClient, settings: Settings) -> dict:
    fresh = _cache.get_fresh()
    if fresh is not None:
        return fresh
    try:
        data = await _fetch(client, settings)
        _cache.set(data)
        return data
    except Exception:
        stale = _cache.get_any()
        if stale is None:
            return {"temp_f": None, "summary": "unknown", "icon": "none", "stale": True}
        return {**stale, "stale": True}