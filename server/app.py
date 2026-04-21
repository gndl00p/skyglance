import asyncio
from datetime import datetime, timezone

import httpx
from fastapi import FastAPI

from server.auth import require_badge_token
from server.config import Settings
from server.schemas import BadgePayload, CalendarTile, CrmTile, DeskTile, WeatherTile
from server.upstreams import calendar as cal
from server.upstreams import weather as weather_mod
from server.upstreams import zoho_crm as crm
from server.upstreams import zoho_desk as desk


def build_app() -> FastAPI:
    settings = Settings()
    app = FastAPI(title="Badger Aggregator")

    @app.get("/badge.json", response_model=BadgePayload, dependencies=[require_badge_token(settings)])
    async def badge_json():
        async with httpx.AsyncClient(timeout=2.0) as client:
            weather, calendar_, desk_, crm_ = await asyncio.gather(
                weather_mod.get(client, settings),
                cal.get(settings),
                desk.get(client, settings),
                crm.get(client, settings),
            )
        return BadgePayload(
            generated_at=datetime.now(timezone.utc).astimezone().isoformat(),
            weather=WeatherTile(**weather),
            calendar=CalendarTile(**calendar_),
            desk=DeskTile(**desk_),
            crm=CrmTile(**crm_),
        )

    return app


app = build_app()