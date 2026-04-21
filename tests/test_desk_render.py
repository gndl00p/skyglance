from tests.fakes.display import FakeDisplay

from desk.render import render


_PAYLOAD = {
    "generated_at": "2026-04-21T10:00:00-05:00",
    "weather": {"temp_f": 72, "summary": "sunny", "icon": "sun", "stale": False},
    "calendar": {"next": {"start": "2026-04-21T15:00:00-05:00", "title": "Standup"}, "stale": False},
    "desk": {"open_tickets": 4, "stale": False},
    "crm": {"tasks_due_today": 2, "stale": False},
}


def test_renders_four_tiles():
    d = FakeDisplay()
    render(d, _PAYLOAD, stale_marker=None)
    texts = " ".join(d.texts())
    assert "72" in texts
    assert "Standup" in texts
    assert "4" in texts
    assert "2" in texts


def test_draws_tile_grid_lines():
    d = FakeDisplay()
    render(d, _PAYLOAD, stale_marker=None)
    lines = [args for name, args in d.calls if name == "line"]
    # one horizontal and one vertical divider
    assert any(a[1] == a[3] for a in lines)  # horizontal
    assert any(a[0] == a[2] for a in lines)  # vertical


def test_stale_marker_rendered():
    d = FakeDisplay()
    render(d, _PAYLOAD, stale_marker="offline")
    texts = " ".join(d.texts())
    assert "offline" in texts


def test_no_calendar_shows_dash():
    d = FakeDisplay()
    payload = dict(_PAYLOAD, calendar={"next": None, "stale": False})
    render(d, payload, stale_marker=None)
    texts = " ".join(d.texts())
    assert "—" in texts or "no events" in texts.lower()


def test_renders_when_payload_none_with_marker():
    d = FakeDisplay()
    render(d, None, stale_marker="offline")
    texts = " ".join(d.texts())
    assert "offline" in texts
