from tests.fakes.display import FakeDisplay

from desk.render import render


_PAYLOAD = {
    "generated_at": "2026-04-21T20:13:00-05:00",
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
        "stale": False,
    },
    "calendar": {"next": None, "stale": True},
    "desk": {"open_tickets": 0, "stale": True},
    "crm": {"tasks_due_today": 0, "stale": True},
}


def test_renders_temp_and_category_large():
    d = FakeDisplay()
    render(d, _PAYLOAD, stale_marker=None)
    text_calls = [(args[0], args[4]) for name, args in d.calls if name == "text"]
    big_texts = [txt for txt, scale in text_calls if scale >= 4]
    assert any("81" in t for t in big_texts)
    assert any("VFR" in t for t in big_texts)


def test_renders_station_wind_clouds():
    d = FakeDisplay()
    render(d, _PAYLOAD, stale_marker=None)
    texts = " ".join(d.texts())
    assert "KLBB" in texts
    assert "190" in texts and "21kt" in texts
    assert "BKN080" in texts


def test_renders_vis_when_available():
    d = FakeDisplay()
    render(d, _PAYLOAD, stale_marker=None)
    texts = " ".join(d.texts())
    assert "10SM" in texts


def test_stale_marker_rendered():
    d = FakeDisplay()
    render(d, _PAYLOAD, stale_marker="offline")
    texts = " ".join(d.texts())
    assert "offline" in texts


def test_payload_none_shows_placeholders():
    d = FakeDisplay()
    render(d, None, stale_marker="offline")
    texts = " ".join(d.texts())
    assert "offline" in texts
    assert "--" in texts


def test_renders_last_updated_hhmm():
    d = FakeDisplay()
    render(d, _PAYLOAD, stale_marker=None)
    texts = " ".join(d.texts())
    assert "20:13" in texts


def test_no_timestamp_when_payload_none():
    d = FakeDisplay()
    render(d, None, stale_marker="offline")
    texts = " ".join(d.texts())
    # Sentinel "--:--" should NOT appear (we just skip the line)
    assert "--:--" not in texts


def test_draws_horizontal_divider():
    d = FakeDisplay()
    render(d, _PAYLOAD, stale_marker=None)
    lines = [args for name, args in d.calls if name == "line"]
    assert any(a[1] == a[3] for a in lines)


def test_low_temp_still_renders():
    payload = dict(_PAYLOAD)
    payload["weather"] = dict(_PAYLOAD["weather"], temp_f=5, flight_category="LIFR")
    d = FakeDisplay()
    render(d, payload, stale_marker=None)
    texts = " ".join(d.texts())
    assert "5F" in texts
    assert "LIFR" in texts
