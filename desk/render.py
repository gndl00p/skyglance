from screens.common import BLACK, HEIGHT, WIDTH, clear_white


def _format_time(iso):
    if "T" not in iso:
        return iso
    t = iso.split("T", 1)[1]
    hhmm = t[:5]
    h = int(hhmm[:2])
    m = hhmm[3:5]
    ampm = "a" if h < 12 else "p"
    h12 = h % 12 or 12
    return f"{h12}:{m}{ampm}"


def _draw_weather(d, tile, x, y, w, h):
    if tile is None:
        d.text("weather: ?", x + 4, y + 4)
        return
    t = tile.get("temp_f")
    s = tile.get("summary", "")
    temp = f"{t}°F" if t is not None else "--°F"
    d.text(temp, x + 4, y + 4, scale=1.4)
    d.text(s, x + 4, y + 28, scale=1.0)
    if tile.get("stale"):
        d.text("(stale)", x + 4, y + 46, scale=0.8)


def _draw_calendar(d, tile, x, y, w, h):
    d.text("Next:", x + 4, y + 4, scale=1.0)
    if tile is None or tile.get("next") is None:
        d.text("— no events —", x + 4, y + 22, scale=1.0)
        return
    nxt = tile["next"]
    when = _format_time(nxt["start"])
    d.text(when, x + 4, y + 22, scale=1.2)
    title = nxt["title"]
    if len(title) > 18:
        title = title[:17] + "…"
    d.text(title, x + 4, y + 44, scale=1.0)
    if tile.get("stale"):
        d.text("(stale)", x + 4, y + 56, scale=0.8)


def _draw_desk(d, tile, x, y, w, h):
    n = tile.get("open_tickets") if tile else None
    label = f"{n}" if n is not None else "?"
    d.text(f"Desk: {label}", x + 4, y + 4, scale=1.2)
    d.text("tickets open", x + 4, y + 28, scale=0.9)
    if tile and tile.get("stale"):
        d.text("(stale)", x + 4, y + 46, scale=0.8)


def _draw_crm(d, tile, x, y, w, h):
    n = tile.get("tasks_due_today") if tile else None
    label = f"{n}" if n is not None else "?"
    d.text(f"CRM: {label}", x + 4, y + 4, scale=1.2)
    d.text("tasks today", x + 4, y + 28, scale=0.9)
    if tile and tile.get("stale"):
        d.text("(stale)", x + 4, y + 46, scale=0.8)


def render(display, payload, stale_marker):
    clear_white(display)
    display.set_pen(BLACK)
    display.set_font("bitmap8")

    mid_x = WIDTH // 2
    mid_y = HEIGHT // 2
    display.line(0, mid_y, WIDTH, mid_y)
    display.line(mid_x, 0, mid_x, HEIGHT)

    if payload is None:
        payload = {}
    _draw_weather(display, payload.get("weather"), 0, 0, mid_x, mid_y)
    _draw_calendar(display, payload.get("calendar"), mid_x, 0, WIDTH - mid_x, mid_y)
    _draw_desk(display, payload.get("desk"), 0, mid_y, mid_x, HEIGHT - mid_y)
    _draw_crm(display, payload.get("crm"), mid_x, mid_y, WIDTH - mid_x, HEIGHT - mid_y)

    if stale_marker:
        display.text(stale_marker, WIDTH - 64, HEIGHT - 10, scale=0.8)

    display.update()
