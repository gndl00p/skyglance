import json
from unittest.mock import patch

import httpx
import pytest
import respx
from fastapi.testclient import TestClient
from freezegun import freeze_time

from server import app as app_module
from server.upstreams import calendar as cal
from server.upstreams import weather as weather_mod
from server.upstreams import zoho_crm as crm
from server.upstreams import zoho_desk as desk


@pytest.fixture(autouse=True)
def env(monkeypatch):
    monkeypatch.setenv("BADGE_TOKEN", "s3cret")
    monkeypatch.setenv("WEATHER_LATITUDE", "30.27")
    monkeypatch.setenv("WEATHER_LONGITUDE", "-97.74")
    monkeypatch.setenv("GOOGLE_SERVICE_ACCOUNT_JSON", "/tmp/x")
    monkeypatch.setenv("GOOGLE_CALENDAR_ID", "x@example.com")
    monkeypatch.setenv("ZOHODESK_CLIENT_ID", "dcid")
    monkeypatch.setenv("ZOHODESK_CLIENT_SECRET", "dcs")
    monkeypatch.setenv("ZOHODESK_REFRESH_TOKEN", "drt")
    monkeypatch.setenv("ZOHODESK_ORG_ID", "42")
    monkeypatch.setenv("ZOHOCRM_CLIENT_ID", "ccid")
    monkeypatch.setenv("ZOHOCRM_CLIENT_SECRET", "ccs")
    monkeypatch.setenv("ZOHOCRM_REFRESH_TOKEN", "crt")
    monkeypatch.setenv("ZOHOCRM_USER_ID", "99")


@pytest.fixture(autouse=True)
def reset_caches():
    for mod in (weather_mod, cal, desk, crm):
        mod._cache.__init__(ttl_seconds=mod._cache.ttl)
    desk._token_cache.__init__(ttl_seconds=desk._token_cache.ttl)
    crm._token_cache.__init__(ttl_seconds=crm._token_cache.ttl)


def _fake_cal_service(items):
    from unittest.mock import MagicMock

    svc = MagicMock()
    svc.events.return_value.list.return_value.execute.return_value = {"items": items}
    return svc


@freeze_time("2026-04-21T10:00:00-05:00")
def test_endpoint_happy_path(fixtures_dir):
    token = json.loads((fixtures_dir / "zoho_oauth_token.json").read_text())
    weather_payload = json.loads((fixtures_dir / "open_meteo_sunny.json").read_text())
    desk_count = json.loads((fixtures_dir / "zoho_desk_count.json").read_text())
    crm_payload = json.loads((fixtures_dir / "zoho_crm_coql.json").read_text())
    cal_items = [{"start": {"dateTime": "2026-04-21T15:00:00-05:00"}, "summary": "Standup"}]

    app = app_module.build_app()
    client = TestClient(app)

    with patch.object(cal, "_build_service", return_value=_fake_cal_service(cal_items)), \
         respx.mock() as m:
        m.post("https://accounts.zoho.com/oauth/v2/token").mock(
            return_value=httpx.Response(200, json=token)
        )
        m.get("https://api.open-meteo.com/v1/forecast").mock(
            return_value=httpx.Response(200, json=weather_payload)
        )
        m.get("https://desk.zoho.com/api/v1/ticketsCount").mock(
            return_value=httpx.Response(200, json=desk_count)
        )
        m.post("https://www.zohoapis.com/crm/v8/coql").mock(
            return_value=httpx.Response(200, json=crm_payload)
        )

        r = client.get("/badge.json", headers={"X-Badge-Token": "s3cret"})

    assert r.status_code == 200
    body = r.json()
    assert body["weather"]["temp_f"] == 72
    assert body["weather"]["icon"] == "sun"
    assert body["weather"]["stale"] is False
    assert body["calendar"]["next"]["title"] == "Standup"
    assert body["desk"]["open_tickets"] == 4
    assert body["crm"]["tasks_due_today"] == 2
    assert "generated_at" in body


def test_endpoint_requires_token():
    app = app_module.build_app()
    r = TestClient(app).get("/badge.json")
    assert r.status_code == 401


def test_endpoint_tile_stale_on_partial_failure(fixtures_dir):
    token = json.loads((fixtures_dir / "zoho_oauth_token.json").read_text())
    weather_payload = json.loads((fixtures_dir / "open_meteo_sunny.json").read_text())
    desk_count = json.loads((fixtures_dir / "zoho_desk_count.json").read_text())

    app = app_module.build_app()
    client = TestClient(app)

    with patch.object(cal, "_build_service", side_effect=RuntimeError("boom")), \
         respx.mock() as m:
        m.post("https://accounts.zoho.com/oauth/v2/token").mock(
            return_value=httpx.Response(200, json=token)
        )
        m.get("https://api.open-meteo.com/v1/forecast").mock(
            return_value=httpx.Response(200, json=weather_payload)
        )
        m.get("https://desk.zoho.com/api/v1/ticketsCount").mock(
            return_value=httpx.Response(200, json=desk_count)
        )
        m.post("https://www.zohoapis.com/crm/v8/coql").mock(
            return_value=httpx.Response(500)
        )

        r = client.get("/badge.json", headers={"X-Badge-Token": "s3cret"})

    body = r.json()
    assert r.status_code == 200
    assert body["weather"]["stale"] is False
    assert body["calendar"]["stale"] is True
    assert body["desk"]["stale"] is False
    assert body["crm"]["stale"] is True