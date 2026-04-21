from pydantic import BaseModel


class WeatherTile(BaseModel):
    temp_f: int | None
    summary: str
    icon: str
    stale: bool = False


class NextEvent(BaseModel):
    start: str
    title: str


class CalendarTile(BaseModel):
    next: NextEvent | None = None
    stale: bool = False


class DeskTile(BaseModel):
    open_tickets: int
    stale: bool = False


class CrmTile(BaseModel):
    tasks_due_today: int
    stale: bool = False


class BadgePayload(BaseModel):
    generated_at: str
    weather: WeatherTile
    calendar: CalendarTile
    desk: DeskTile
    crm: CrmTile