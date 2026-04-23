from screens.common import BLACK, HEIGHT, WIDTH, clear_white


def _weather(payload):
    return (payload or {}).get("weather") or {}


def _hhmm(iso):
    if not iso or "T" not in iso:
        return None
    t = iso.split("T", 1)[1]
    return t[:5]


def render(display, payload, stale_marker):
    clear_white(display)
    display.set_pen(BLACK)

    w = _weather(payload)
    temp = w.get("temp_f")
    cat = w.get("flight_category") or "--"
    station = w.get("station") or "----"
    wind = w.get("wind") or "--"
    sky = w.get("summary") or "--"
    vis = w.get("visibility_sm")
    updated = _hhmm((payload or {}).get("generated_at"))

    display.set_font("bitmap8")

    # Top-left: big temperature.
    temp_str = f"{int(temp)}F" if temp is not None else "--F"
    display.text(temp_str, 8, 10, scale=5)

    # Top-right: big flight category.
    cat_x = WIDTH - (len(cat) * 30) - 8
    display.text(cat, cat_x, 10, scale=5)

    # Divider.
    display.line(0, 64, WIDTH, 64)

    # Middle: station + visibility.
    line1 = station
    if vis is not None:
        line1 += f"  vis {int(vis)}SM" if vis == int(vis) else f"  vis {vis}SM"
    display.text(line1, 8, 72, scale=2)

    # Wind line.
    display.text(wind, 8, 90, scale=2)

    # Clouds line.
    display.text(sky, 8, 108, scale=2)

    # Last updated HH:MM top-right corner.
    if updated is not None:
        display.text(updated, WIDTH - 48, 4, scale=1)

    if stale_marker:
        display.text(stale_marker, WIDTH - 56, HEIGHT - 8, scale=1)

    display.update()
