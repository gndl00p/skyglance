import store


def test_load_missing_returns_defaults(tmp_path):
    p = tmp_path / "state.json"
    assert store.load(str(p)) == {"last_data": None}


def test_load_empty_file_returns_defaults(tmp_path):
    p = tmp_path / "state.json"
    p.write_text("")
    assert store.load(str(p)) == {"last_data": None}


def test_load_bad_json_returns_defaults(tmp_path):
    p = tmp_path / "state.json"
    p.write_text("{not json")
    assert store.load(str(p)) == {"last_data": None}


def test_round_trip(tmp_path):
    p = tmp_path / "state.json"
    payload = {"last_data": {"temp_f": 72, "station": "KLBB"}}
    store.save(str(p), payload)
    assert store.load(str(p)) == payload


def test_save_overwrites(tmp_path):
    p = tmp_path / "state.json"
    store.save(str(p), {"last_data": {"temp_f": 72}})
    store.save(str(p), {"last_data": {"temp_f": 75}})
    assert store.load(str(p))["last_data"]["temp_f"] == 75
