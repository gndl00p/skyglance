from types import SimpleNamespace
from unittest.mock import patch

from tests.fakes.display import FakeDisplay

import main


def _cfg():
    return SimpleNamespace(
        WIFI_SSID="n", WIFI_PSK="p",
        METAR_STATION="KLBB",
        REFRESH_MINUTES=15,
    )


def test_cycle_saves_on_fresh_fetch(tmp_path, monkeypatch):
    p = tmp_path / "state.json"
    p.write_text("{}")
    d = FakeDisplay()

    metar = {"temp_f": 72, "station": "KLBB", "flight_category": "VFR",
             "wind": "180 5kt", "summary": "CLR", "updated_z": "20:00",
             "visibility_sm": 10.0, "ceiling_ft": None, "raw": "",
             "stale": False}

    monkeypatch.setattr(main, "fetch", lambda cfg, last: (metar, None))

    main._cycle(d, _cfg(), str(p))

    import json
    state = json.loads(p.read_text())
    assert state["last_data"] == metar
    assert "72" in " ".join(d.texts())


def test_cycle_offline_uses_last_data(tmp_path, monkeypatch):
    p = tmp_path / "state.json"
    last = {"temp_f": 69, "station": "KLBB", "flight_category": "VFR",
            "wind": "180 10kt", "summary": "CLR", "updated_z": "19:30",
            "visibility_sm": 10.0, "ceiling_ft": None, "raw": "",
            "stale": False}
    import json
    p.write_text(json.dumps({"last_data": last}))

    d = FakeDisplay()
    monkeypatch.setattr(main, "fetch", lambda cfg, prev: ({**prev, "stale": True}, "offline"))

    main._cycle(d, _cfg(), str(p))

    texts = " ".join(d.texts())
    assert "69" in texts
    assert "offline" in texts