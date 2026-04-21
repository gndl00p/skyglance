import httpx

from server.cache import TTLCache
from server.config import Settings

_cache = TTLCache(ttl_seconds=300)


def _c_to_f(c):
    if c is None:
        return None
    return int(round(c * 9 / 5 + 32))


def _parse_vis(v):
    if v is None:
        return None
    s = str(v).replace("+", "").strip()
    if not s:
        return None
    if "/" in s:
        total = 0.0
        for token in s.split():
            if "/" in token:
                num, den = token.split("/")
                total += float(num) / float(den)
            else:
                total += float(token)
        return total
    try:
        return float(s)
    except ValueError:
        return None


def _ceiling_ft(clouds):
    if not clouds:
        return None
    for layer in clouds:
        cover = str(layer.get("cover", "")).upper()
        base = layer.get("base")
        if cover in ("BKN", "OVC", "VV") and base is not None:
            return int(base)
    return None


def _flight_category(ceiling_ft, vis_sm):
    c = ceiling_ft
    v = vis_sm
    if (c is not None and c < 500) or (v is not None and v < 1):
        return "LIFR"
    if (c is not None and c < 1000) or (v is not None and v < 3):
        return "IFR"
    if (c is not None and c <= 3000) or (v is not None and v <= 5):
        return "MVFR"
    return "VFR"


def _format_wind(wdir, wspd, wgst):
    if wspd is None or wspd == 0:
        return "CALM"
    if wdir is None or (isinstance(wdir, str) and wdir.upper() == "VRB") or wdir == 0:
        base = f"VRB {int(wspd)}kt"
    else:
        base = f"{int(wdir):03d} {int(wspd)}kt"
    if wgst:
        base += f" G{int(wgst)}"
    return base


def _summarize_clouds(clouds):
    if not clouds:
        return "CLR"
    parts = []
    for layer in clouds:
        cover = str(layer.get("cover", "")).upper()
        if cover in ("CLR", "SKC", "NCD"):
            return "CLR"
        base = layer.get("base")
        if base is not None:
            # METAR cloud base codes are hundreds of feet: 8000 ft → "080".
            parts.append(f"{cover}{int(base / 100):03d}")
        else:
            parts.append(cover)
        if len(parts) == 3:
            break
    return " ".join(parts)


_EMPTY = {
    "temp_f": None,
    "summary": "no data",
    "icon": "none",
    "flight_category": None,
    "station": None,
    "wind": None,
    "visibility_sm": None,
    "ceiling_ft": None,
    "raw": None,
    "stale": False,
}


def _parse(payload):
    if not payload:
        out = dict(_EMPTY)
        out["stale"] = True
        return out
    m = payload[0]
    temp_f = _c_to_f(m.get("temp"))
    vis_sm = _parse_vis(m.get("visib"))
    ceiling = _ceiling_ft(m.get("clouds"))
    cat = _flight_category(ceiling, vis_sm)
    return {
        "temp_f": temp_f,
        "summary": _summarize_clouds(m.get("clouds")),
        "icon": "sun" if cat == "VFR" else "cloud",
        "flight_category": cat,
        "station": m.get("icaoId") or m.get("station") or None,
        "wind": _format_wind(m.get("wdir"), m.get("wspd"), m.get("wgst")),
        "visibility_sm": vis_sm,
        "ceiling_ft": ceiling,
        "raw": m.get("rawOb"),
        "stale": False,
    }


async def _fetch(client: httpx.AsyncClient, settings: Settings) -> dict:
    r = await client.get(
        "https://aviationweather.gov/api/data/metar",
        params={"ids": settings.metar_station, "format": "json"},
        timeout=5.0,
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
            out = dict(_EMPTY)
            out["stale"] = True
            return out
        return {**stale, "stale": True}
