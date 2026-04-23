# Copy to config.py on the device (or deploy via tools/flash.sh).

WIFI_SSID = "REPLACE-ME"
WIFI_PSK = "REPLACE-ME"

# Any ICAO airport identifier — KLBB, KAUS, EGLL, YSSY, RJTT, etc.
METAR_STATION = "KLBB"

# How often to re-fetch the METAR. aviationweather.gov updates hourly;
# 15 min is a polite cadence.
REFRESH_MINUTES = 15
