from types import SimpleNamespace
from unittest.mock import MagicMock

from tests.fakes.display import FakeDisplay

import modes.desk as desk_mod


def _cfg():
    return SimpleNamespace(
        WIFI_SSID="n", WIFI_PSK="p",
        AGGREGATOR_URL="http://h/badge.json",
        AGGREGATOR_TOKEN="t",
        REFRESH_MINUTES=15,
    )


def test_refresh_cycle_persists_and_renders(monkeypatch):
    d = FakeDisplay()
    payload = {"weather": {"temp_f": 72, "summary": "sunny", "icon": "sun", "stale": False},
               "calendar": {"next": None, "stale": False},
               "desk": {"open_tickets": 0, "stale": False},
               "crm": {"tasks_due_today": 0, "stale": False}}

    monkeypatch.setattr(desk_mod, "fetch", lambda cfg, last: (payload, None))
    save_calls = []
    monkeypatch.setattr(desk_mod, "save_state", lambda p, s: save_calls.append((p, s)))
    load_calls = []
    monkeypatch.setattr(desk_mod, "load_state", lambda p: load_calls.append(p) or {"mode": "desk", "last_data": None})

    controller = desk_mod.DeskMode(d, _cfg(), state_path="/state.json")
    controller.cycle()

    texts = " ".join(d.texts())
    assert "72" in texts
    assert save_calls, "state.save not called"
    assert save_calls[0][1]["last_data"] == payload


def test_offline_uses_last_data(monkeypatch):
    d = FakeDisplay()
    last = {"weather": {"temp_f": 69, "summary": "cloud", "icon": "cloud", "stale": False},
            "calendar": {"next": None, "stale": False},
            "desk": {"open_tickets": 1, "stale": False},
            "crm": {"tasks_due_today": 0, "stale": False}}

    monkeypatch.setattr(desk_mod, "load_state", lambda p: {"mode": "desk", "last_data": last})
    monkeypatch.setattr(desk_mod, "fetch", lambda cfg, ld: (ld, "offline"))
    monkeypatch.setattr(desk_mod, "save_state", lambda p, s: None)

    controller = desk_mod.DeskMode(d, _cfg(), state_path="/state.json")
    controller.cycle()

    texts = " ".join(d.texts())
    assert "69" in texts
    assert "offline" in texts


def test_button_a_forces_refresh(monkeypatch):
    d = FakeDisplay()
    fetches = []

    def fake_fetch(cfg, last):
        fetches.append(last)
        return ({"weather": None, "calendar": None, "desk": None, "crm": None}, "offline")

    monkeypatch.setattr(desk_mod, "load_state", lambda p: {"mode": "desk", "last_data": None})
    monkeypatch.setattr(desk_mod, "fetch", fake_fetch)
    monkeypatch.setattr(desk_mod, "save_state", lambda p, s: None)

    controller = desk_mod.DeskMode(d, _cfg(), state_path="/state.json")
    controller.handle_button("A")
    assert len(fetches) == 1
