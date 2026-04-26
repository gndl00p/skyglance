from tests.fakes.display import FakeDisplay

from render import render


_WEATHER = {
    "temp_f": 86,
    "dewpoint_f": 46,
    "summary": "FEW050",
    "flight_category": "VFR",
    "station": "KLBB",
    "station_name": "Lubbock",
    "wind": "200 5kt G15",
    "wind_deg": 200,
    "wind_kt": 5,
    "visibility_sm": 10.0,
    "ceiling_ft": None,
    "raw": "KLBB 232200Z 20005G15KT 10SM FEW050 30/M04 A2998",
    "updated_z": "22:00",
    "updated_hour_local": 17,
    "altimeter_inhg": 29.92,
    "spread_f": 40,
    "density_altitude_ft": 5800,
    "pressure_altitude_ft": 3500,
    "elevation_ft": 3282,
    "lat": 33.66,
    "lon": -101.82,
    "sunrise_local": "06:45",
    "sunset_local": "20:15",
    "stale": False,
}


def test_renders_header_with_station_and_name():
    d = FakeDisplay()
    render(d, _WEATHER)
    texts = [args[0] for name, args in d.calls if name == "text"]
    assert any("KLBB" in t and "Lubbock" in t for t in texts)


def test_renders_observation_time_in_header():
    d = FakeDisplay()
    render(d, _WEATHER)
    texts = " ".join([args[0] for name, args in d.calls if name == "text"])
    assert "22:00Z" in texts


def test_renders_big_temp_and_category():
    d = FakeDisplay()
    render(d, _WEATHER)
    big = [args[0] for name, args in d.calls if name == "text" and args[4] >= 4]
    assert any("86" in t for t in big)
    assert any("VFR" in t for t in big)


def test_data_grid_labels_present():
    d = FakeDisplay()
    render(d, _WEATHER)
    texts = " ".join([args[0] for name, args in d.calls if name == "text"])
    assert "WIND" in texts
    assert "VIS" in texts
    assert "T/Td" in texts
    assert "DA" in texts
    assert "CLD" in texts
    assert "CEIL" in texts


def test_renders_visibility_in_grid():
    d = FakeDisplay()
    render(d, _WEATHER)
    texts = " ".join([args[0] for name, args in d.calls if name == "text"])
    assert "10 SM" in texts


def test_renders_density_altitude_in_grid():
    d = FakeDisplay()
    render(d, _WEATHER)
    texts = " ".join([args[0] for name, args in d.calls if name == "text"])
    assert "5800 ft" in texts


def test_renders_temp_dewpoint_in_grid():
    d = FakeDisplay()
    render(d, _WEATHER)
    texts = " ".join([args[0] for name, args in d.calls if name == "text"])
    assert "86/46" in texts


def test_renders_sunrise_sunset():
    d = FakeDisplay()
    render(d, _WEATHER)
    texts = " ".join([args[0] for name, args in d.calls if name == "text"])
    assert "SR 06:45" in texts
    assert "SS 20:15" in texts


def test_renders_runway_when_configured():
    d = FakeDisplay()
    w = dict(_WEATHER, runway_heading_deg=170, headwind_kt=12,
             crosswind_kt=5, crosswind_side="L")
    render(d, w)
    texts = [args[0] for name, args in d.calls if name == "text"]
    rwy = [t for t in texts if t.startswith("RWY")]
    assert rwy
    assert "RWY17" in rwy[0]
    assert "HW 12" in rwy[0]
    assert "XW 5L" in rwy[0]


def test_no_runway_line_when_not_configured():
    d = FakeDisplay()
    render(d, _WEATHER)
    rwy = [args[0] for name, args in d.calls if name == "text" and args[0].startswith("RWY")]
    assert not rwy


def test_inverted_category_for_ifr():
    d = FakeDisplay()
    w = dict(_WEATHER, flight_category="IFR")
    render(d, w)
    rects = [args for name, args in d.calls if name == "rectangle"]
    big_rects = [r for r in rects if 14 <= r[1] <= 20 and r[3] >= 40]
    assert big_rects
    pens = [args[0] for name, args in d.calls if name == "set_pen"]
    assert 15 in pens


def test_plain_category_for_vfr():
    d = FakeDisplay()
    render(d, _WEATHER)
    pens = [args[0] for name, args in d.calls if name == "set_pen"]
    # First pen is background, then foreground; no extra pen-flips for inversion
    # (the only pens are bg=15 and fg=0 in non-night mode).
    assert set(pens) <= {0, 15}
    rects = [args for name, args in d.calls if name == "rectangle"]
    # Only the full-screen clear rect at (0,0,W,H).
    assert len(rects) == 1


def test_two_dividers_drawn():
    d = FakeDisplay()
    render(d, _WEATHER)
    lines = [args for name, args in d.calls if name == "line"]
    # header divider at y=12, hero divider at y=72
    ys = sorted({(a[1], a[3]) for a in lines})
    assert (12, 12) in ys
    assert (72, 72) in ys


def test_night_inverts_colors():
    d = FakeDisplay()
    render(d, _WEATHER, invert=True)
    pens = [args[0] for name, args in d.calls if name == "set_pen"]
    assert pens[0] == 0  # background = BLACK in night mode


def test_day_normal_colors():
    d = FakeDisplay()
    render(d, _WEATHER, invert=False)
    pens = [args[0] for name, args in d.calls if name == "set_pen"]
    assert pens[0] == 15


def test_low_temp():
    w = dict(_WEATHER, temp_f=5, flight_category="LIFR")
    d = FakeDisplay()
    render(d, w)
    big = [args[0] for name, args in d.calls if name == "text" and args[4] >= 4]
    assert any("5F" in t for t in big)
    assert any("LIFR" in t for t in big)


def test_stale_marker_replaces_runway_slot():
    d = FakeDisplay()
    render(d, _WEATHER, stale_marker="offline")
    texts = " ".join([args[0] for name, args in d.calls if name == "text"])
    assert "offline" in texts


def test_none_weather_safe():
    d = FakeDisplay()
    render(d, None, stale_marker="offline")
    texts = " ".join([args[0] for name, args in d.calls if name == "text"])
    assert "offline" in texts
    # No crash, placeholders rendered
    assert "--F" in texts or "--" in texts
