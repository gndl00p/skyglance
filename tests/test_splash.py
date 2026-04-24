from tests.fakes.display import FakeDisplay

import splash


def test_shows_name_and_tagline():
    d = FakeDisplay()
    splash.render(d)
    texts = " ".join(d.texts())
    assert "SkyGlance" in texts
    assert "aviation weather" in texts


def test_version_rendered():
    d = FakeDisplay()
    splash.render(d, version="v1.2.3")
    texts = " ".join(d.texts())
    assert "v1.2.3" in texts


def test_does_a_full_refresh():
    d = FakeDisplay()
    splash.render(d)
    speeds = [args[0] for name, args in d.calls if name == "set_update_speed"]
    assert 0 in speeds
