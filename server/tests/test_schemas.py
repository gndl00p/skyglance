from server.schemas import BadgePayload, WeatherTile, CalendarTile, DeskTile, CrmTile, NextEvent


def test_payload_round_trip():
    p = BadgePayload(
        generated_at="2026-04-21T10:00:00-05:00",
        weather=WeatherTile(temp_f=72, summary="sunny", icon="sun"),
        calendar=CalendarTile(next=NextEvent(start="2026-04-21T15:00:00-05:00", title="Standup")),
        desk=DeskTile(open_tickets=4),
        crm=CrmTile(tasks_due_today=2),
    )
    data = p.model_dump()
    assert data["weather"]["temp_f"] == 72
    assert data["weather"]["stale"] is False
    assert data["calendar"]["next"]["title"] == "Standup"
    assert data["desk"]["open_tickets"] == 4
    assert data["crm"]["tasks_due_today"] == 2


def test_calendar_tile_allows_null_next():
    t = CalendarTile(next=None)
    assert t.model_dump()["next"] is None


def test_stale_defaults_false():
    assert WeatherTile(temp_f=None, summary="unknown", icon="none").model_dump()["stale"] is False
    assert WeatherTile(temp_f=None, summary="unknown", icon="none", stale=True).model_dump()["stale"] is True