from tests.fakes.display import FakeDisplay

import screens.common as common


def test_clear_white_fills_background():
    d = FakeDisplay()
    common.clear_white(d)
    assert ("set_pen", (15,)) in d.calls
    assert any(name == "rectangle" for name, _ in d.calls)
    assert ("set_pen", (0,)) in d.calls


def test_draw_qr_renders_modules():
    d = FakeDisplay()
    common.draw_qr(d, "https://robb.tech", x=200, y=30, size_px=60)
    pixel_calls = [args for name, args in d.calls if name == "rectangle" or name == "pixel"]
    assert len(pixel_calls) > 0


def test_draw_header_rule():
    d = FakeDisplay()
    common.draw_header_rule(d, y=20)
    line_calls = [args for name, args in d.calls if name == "line"]
    assert line_calls == [(0, 20, 296, 20)]


def test_wrap_text_into_lines():
    lines = common.wrap("one two three four five", max_chars=8)
    assert lines == ["one two", "three", "four", "five"]