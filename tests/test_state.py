from pathlib import Path

import state


def test_load_missing_returns_defaults(tmp_path):
    p = tmp_path / "state.json"
    assert state.load(str(p)) == {"mode": "badge", "last_data": None}


def test_load_empty_file_returns_defaults(tmp_path):
    p = tmp_path / "state.json"
    p.write_text("")
    assert state.load(str(p)) == {"mode": "badge", "last_data": None}


def test_load_bad_json_returns_defaults(tmp_path):
    p = tmp_path / "state.json"
    p.write_text("{not json")
    assert state.load(str(p)) == {"mode": "badge", "last_data": None}


def test_round_trip(tmp_path):
    p = tmp_path / "state.json"
    payload = {"mode": "desk", "last_data": {"weather": {"temp_f": 70}}}
    state.save(str(p), payload)
    assert state.load(str(p)) == payload


def test_save_overwrites(tmp_path):
    p = tmp_path / "state.json"
    state.save(str(p), {"mode": "badge", "last_data": None})
    state.save(str(p), {"mode": "desk", "last_data": None})
    assert state.load(str(p))["mode"] == "desk"