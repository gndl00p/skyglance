# Badger Aggregator

FastAPI service that fans out to external APIs, caches and normalises
the responses, and serves a single token-gated JSON blob to the Badger
2040 W desk-mode display.

## Endpoint

```
GET /badge.json
    Header: X-Badge-Token: <BADGE_TOKEN>
```

### Response shape

```json
{
  "generated_at": "2026-04-23T16:13:02.469075-05:00",
  "weather": {
    "temp_f": 81,
    "summary": "FEW060 BKN080",
    "icon": "cloud",
    "flight_category": "VFR",
    "station": "KLBB",
    "wind": "190 21kt G27",
    "visibility_sm": 10.0,
    "ceiling_ft": 8000,
    "raw": "KLBB 212013Z 19021G27KT 10SM FEW060 BKN080 27/14 A3002",
    "stale": false
  },
  "calendar": {
    "next": { "start": "2026-04-21T15:00:00-05:00", "title": "Standup" },
    "stale": false
  },
  "desk": { "open_tickets": 4, "stale": false },
  "crm":  { "tasks_due_today": 2, "stale": false }
}
```

### Auth

`X-Badge-Token` must match the server's `BADGE_TOKEN` env variable
exactly. Anything else returns `401`.

### Failure semantics

Each tile carries a `stale: bool` flag. On upstream error the aggregator
returns the last successful value (if any) with `stale: true`; when
nothing has succeeded yet it returns a safe default (e.g.
`open_tickets: 0`) with `stale: true`. The endpoint itself always
returns `200` so the device renders a best-effort frame rather than
blanking the screen.

## Architecture

```
  fastapi.FastAPI
       |
       |  @app.get("/badge.json") depends=[require_badge_token]
       v
  asyncio.gather(
      weather.get(httpx_client, settings),    # METAR
      calendar.get(settings),                 # Google Calendar (sync lib)
      zoho_desk.get(httpx_client, settings),  # /api/v1/ticketsCount
      zoho_crm.get(httpx_client, settings),   # COQL
  )
       |
       v
  BadgePayload(...)  (pydantic v2)
```

Each upstream module encapsulates a small `TTLCache` (weather 300 s,
calendar 60 s, Zoho 30 s data / 3000 s OAuth access token) and owns the
stale-fallback behaviour. The endpoint never blocks longer than the
httpx client's 2 s timeout because upstreams run concurrently.

## Run (dev)

```bash
cd ~/code/badger
python3 -m venv server/.venv
server/.venv/bin/pip install -r server/requirements-dev.txt

cp server/.env.example server/.env
# edit server/.env — fill in BADGE_TOKEN + METAR_STATION at minimum

server/.venv/bin/uvicorn server.app:app \
    --host 0.0.0.0 --port 8088 --env-file server/.env
```

## Test

```bash
server/.venv/bin/pytest server/tests -v
```

34 tests. Fully offline — HTTP upstreams are stubbed with `respx`,
Google's sync library is patched with `unittest.mock`, and `freezegun`
pins `datetime.date.today()` where COQL queries reference it.

## Deploy as a user systemd unit

```bash
mkdir -p ~/.config/systemd/user
ln -sf "$(pwd)/server/badger.service" ~/.config/systemd/user/badger.service
systemctl --user daemon-reload
systemctl --user enable --now badger
systemctl --user status badger
journalctl --user -u badger -f    # follow logs
```

The unit uses `%h` so it works for any user without modification.
`EnvironmentFile=%h/code/badger/server/.env` means credentials live
in one place and only one place.

## Modules

| File                               | Responsibility                                       |
| ---------------------------------- | ---------------------------------------------------- |
| `app.py`                           | FastAPI app factory + `/badge.json` endpoint         |
| `auth.py`                          | `X-Badge-Token` header dependency                    |
| `cache.py`                         | Single-entry `TTLCache` used by every upstream       |
| `config.py`                        | Pydantic `Settings` loaded from `.env`               |
| `schemas.py`                       | Response Pydantic models                             |
| `upstreams/weather.py`             | METAR fetch + parse + flight-category classifier     |
| `upstreams/calendar.py`            | Google Calendar next-event lookup                    |
| `upstreams/zoho_desk.py`           | Open-ticket count with OAuth refresh                 |
| `upstreams/zoho_crm.py`            | Today's open Tasks via COQL                          |

## Adding a new upstream

1. Create `server/upstreams/<name>.py` exposing `async def get(client, settings)` and a module-level `_cache = TTLCache(...)`.
2. Add a Pydantic tile to `server/schemas.py` and include it in `BadgePayload`.
3. Wire into `server/app.py`'s `asyncio.gather` call and pass its result into the matching tile model.
4. Mirror the test pattern from `server/tests/test_weather.py`:
   happy path, cached-within-ttl, stale-fallback-on-error,
   default-when-never-succeeded. Use `respx.mock()` for HTTP upstreams,
   `unittest.mock.patch.object` for sync clients that cannot be
   intercepted at the HTTP layer.
