from tests.fakes.display import FakeDisplay

import raw


def test_renders_raw_metar():
    d = FakeDisplay()
    raw.render(d, "KLBB 232200Z 23005KT 10SM FEW050 31/M06 A2998")
    texts = " ".join(d.texts())
    assert "Raw METAR" in texts
    assert "KLBB" in texts
    assert "23005KT" in texts


def test_header_and_back_hint():
    d = FakeDisplay()
    raw.render(d, "anything")
    texts = " ".join(d.texts())
    assert "Raw METAR" in texts
    assert "B back" in texts


def test_missing_raw_shows_placeholder():
    d = FakeDisplay()
    raw.render(d, "")
    texts = " ".join(d.texts())
    assert "no data" in texts


def test_none_raw_shows_placeholder():
    d = FakeDisplay()
    raw.render(d, None)
    texts = " ".join(d.texts())
    assert "no data" in texts


def test_wraps_long_metar():
    d = FakeDisplay()
    long_metar = " ".join(["TOKEN{0}".format(i) for i in range(20)])
    raw.render(d, long_metar)
    text_lines = [args[0] for name, args in d.calls if name == "text" and args[4] >= 2 and args[0] != "Raw METAR"]
    assert len(text_lines) >= 3


def test_overflow_indicator_when_many_lines():
    d = FakeDisplay()
    long_metar = " ".join(["XXX{0}".format(i) for i in range(40)])
    raw.render(d, long_metar)
    texts = " ".join(d.texts())
    assert "more" in texts


def test_divider_drawn():
    d = FakeDisplay()
    raw.render(d, "KLBB 232200Z")
    lines = [args for name, args in d.calls if name == "line"]
    assert any(a[1] == 24 for a in lines)
