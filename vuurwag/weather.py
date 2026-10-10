"""Local weather from Open-Meteo (free, no key), cached and offline-safe, plus sun and moon maths.

- Geocoding: https://geocoding-api.open-meteo.com/v1/search?name=...  (once per place, cached)
- Current conditions: https://api.open-meteo.com/v1/forecast?...&current=...  (every 10 min)
- No network: the last good reading is used while it is younger than an hour, then the
  scene falls back to the clock and shows a "no weather" badge.
- Demo mode cycles through every condition so every effect can be seen.
"""
from __future__ import annotations

import asyncio
import json
import math
import os
import time
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Awaitable, Callable

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
CURRENT_FIELDS = ("temperature_2m,relative_humidity_2m,apparent_temperature,is_day,precipitation,rain,showers,"
                  "weather_code,cloud_cover,wind_speed_10m,wind_direction_10m,wind_gusts_10m")
DEFAULT_PLACE = "Pierre van Ryneveld, Centurion, South Africa"
PRETORIA_LABEL = "Pretoria"
PRETORIA = (-25.74486, 28.18783)
REFRESH_SECONDS = 600.0
VIEW_AZ = 300.0   # the camera looks west-north-west: sunsets over the back wall, north to the right
STALE_SECONDS = 3600.0

CONDITIONS = ["clear", "partly", "cloudy", "overcast", "fog", "drizzle", "rain", "heavy", "storm", "snow"]
LABELS = {
    "clear": "Clear", "partly": "Partly cloudy", "cloudy": "Mostly cloudy", "overcast": "Overcast", "fog": "Fog",
    "drizzle": "Drizzle", "rain": "Rain", "heavy": "Heavy rain", "storm": "Thunderstorm", "snow": "Snow",
}
WMO_LABELS = {
    0: "Clear", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast", 45: "Fog", 48: "Rime fog",
    51: "Light drizzle", 53: "Drizzle", 55: "Dense drizzle", 56: "Freezing drizzle", 57: "Freezing drizzle",
    61: "Light rain", 63: "Rain", 65: "Heavy rain", 66: "Freezing rain", 67: "Freezing rain",
    71: "Light snow", 73: "Snow", 75: "Heavy snow", 77: "Snow grains", 80: "Rain showers", 81: "Rain showers",
    82: "Violent showers", 85: "Snow showers", 86: "Snow showers", 95: "Thunderstorm", 96: "Storm + hail", 99: "Storm + hail",
}


def condition_for(code: int, cloud_cover: float | None = None) -> str:
    """Map a WMO weather code (+ cloud cover) to one of CONDITIONS."""
    cc = cloud_cover if cloud_cover is not None else -1
    if code in (0, 1):
        if cc >= 75:
            return "cloudy"
        if cc >= 35:
            return "partly"
        return "clear"
    if code == 2:
        return "cloudy" if cc >= 70 else "partly"
    if code == 3:
        return "overcast"
    if code in (45, 48):
        return "fog"
    if code in (51, 53, 55, 56, 57):
        return "drizzle"
    if code in (61, 63, 66, 67, 80, 81):
        return "rain"
    if code in (65, 82):
        return "heavy"
    if code in (71, 73, 75, 77, 85, 86):
        return "snow"
    if code in (95, 96, 99):
        return "storm"
    return "partly"


@dataclass
class Place:
    name: str
    lat: float
    lon: float
    country_code: str | None = None
    admin1: str | None = None
    timezone: str | None = None


@dataclass
class Weather:
    place: str = "Pretoria"
    lat: float = PRETORIA[0]
    lon: float = PRETORIA[1]
    temp: float | None = None
    feels: float | None = None
    humidity: float | None = None
    is_day: bool | None = None
    precipitation: float = 0.0
    rain: float = 0.0
    showers: float = 0.0
    code: int = 0
    cloud_cover: float = 0.0
    wind_kmh: float = 0.0
    wind_dir: float = 270.0
    gusts_kmh: float = 0.0
    observed: str | None = None
    fetched_at: float = field(default_factory=time.time)
    source: str = "open-meteo"   # open-meteo | cache | demo | forced

    @property
    def condition(self) -> str:
        return condition_for(self.code, self.cloud_cover)

    @property
    def label(self) -> str:
        if self.source in ("demo", "forced"):
            return LABELS[self.condition]
        return WMO_LABELS.get(self.code, LABELS[self.condition])

    @property
    def cloud(self) -> float:
        base = {"clear": 0.08, "partly": 0.4, "cloudy": 0.7, "overcast": 0.95, "fog": 0.6, "drizzle": 0.85,
                "rain": 0.95, "heavy": 1.0, "storm": 1.0, "snow": 0.95}[self.condition]
        return max(base, min(1.0, self.cloud_cover / 100.0)) if self.condition != "clear" else min(0.3, self.cloud_cover / 100.0)

    @property
    def rain_intensity(self) -> float:
        base = {"drizzle": 0.22, "rain": 0.55, "heavy": 0.95, "storm": 0.85, "snow": 0.5}.get(self.condition, 0.0)
        mm = max(self.precipitation, self.rain + self.showers)
        return max(base, min(1.0, mm / 6.0)) if base else 0.0

    @property
    def wind_x(self) -> float:
        """Signed screen-space wind (+ = blowing to the right), km/h, for a view facing VIEW_AZ."""
        return math.sin(math.radians(self.wind_dir + 180.0 - VIEW_AZ)) * self.wind_kmh

    @property
    def age(self) -> float:
        return time.time() - self.fetched_at


COUNTRIES = {"south africa": "ZA", "za": "ZA", "rsa": "ZA", "namibia": "NA", "botswana": "BW", "zimbabwe": "ZW",
             "lesotho": "LS", "eswatini": "SZ", "mozambique": "MZ", "united kingdom": "GB", "uk": "GB",
             "australia": "AU", "new zealand": "NZ", "united states": "US", "usa": "US", "netherlands": "NL"}


def split_place(place: str) -> tuple[str, str | None]:
    """'Town, ZA' -> ('Town', 'ZA'); 'Suburb, Town, South Africa' -> ('Suburb, Town', 'ZA'); 'Town' -> ('Town', None)."""
    if "," in place:
        name, _, tail = place.rpartition(",")
        tail = tail.strip()
        cc = COUNTRIES.get(tail.lower()) or (tail.upper() if len(tail) == 2 and tail.isalpha() else None)
        if cc:
            return name.strip(), cc
    return place.strip(), None


def country_hint(place: str) -> str | None:
    """The last part of 'Town, Country' when it is not a country (or ISO code) in COUNTRIES: 'Lyon, France' ->
    'France'. The geocoder then searches without a country filter and prefers results in that country."""
    if "," not in place:
        return None
    name, cc = split_place(place)
    if cc:
        return None
    tail = place.rpartition(",")[2].strip()
    return tail or None


def geocode_candidates(place: str) -> list[tuple[str, str | None, bool]]:
    """Names to try, most specific first: (name, country code, is_fallback).

    Open-Meteo's geocoder matches a single place name, so 'Pierre van Ryneveld, Centurion, South Africa'
    becomes 'Pierre van Ryneveld' (ZA), then 'Centurion' (ZA) as the fallback. Any country works: a name or an
    ISO code in COUNTRIES becomes a filter; any other last part ('Lyon, France', 'Hatfield, Pretoria') is searched
    last, without a filter, as the fallback town, and also used to pick among the results (see country_hint).
    """
    name, cc = split_place(place)
    hint = country_hint(place)
    if hint:
        name = place.rpartition(",")[0]
    parts = [p.strip() for p in name.split(",") if p.strip()]
    out: list[tuple[str, str | None, bool]] = []
    if parts:
        out.append((parts[0], cc, False))
    for extra in parts[1:]:
        out.append((extra, cc, True))
    if len(parts) > 1 and (name, cc, False) not in out:
        out.insert(0, (name, cc, False))
    if hint:
        # 'Hatfield, Pretoria': the last part may be the town rather than a country - keep it as the final fallback
        out.append((hint, None, True))
    return out or [(place, None, False)]


def geocode_url(place: str, cc: str | None = None) -> str:
    if cc is None:
        place, cc = split_place(place)
    q = {"name": place, "count": "5", "language": "en", "format": "json"}
    if cc:
        q["countryCode"] = cc
    return GEOCODE_URL + "?" + urllib.parse.urlencode(q)


def forecast_url(lat: float, lon: float) -> str:
    q = {"latitude": f"{lat:.4f}", "longitude": f"{lon:.4f}", "current": CURRENT_FIELDS, "timezone": "auto"}
    return FORECAST_URL + "?" + urllib.parse.urlencode(q, safe=",")


def parse_geocode(doc: dict[str, Any], place: str = "") -> Place | None:
    results = doc.get("results") or []
    if not results:
        return None
    _, cc = split_place(place) if place else ("", None)
    hint = (country_hint(place) or "").lower() if place else ""
    best = results[0]
    if cc:
        for r in results:
            if str(r.get("country_code", "")).upper() == cc:
                best = r
                break
    elif hint:
        for r in results:
            if hint in (str(r.get("country", "")).lower(), str(r.get("country_code", "")).lower()):
                best = r
                break
    return Place(name=str(best.get("name") or place), lat=float(best["latitude"]), lon=float(best["longitude"]),
                 country_code=best.get("country_code"), admin1=best.get("admin1"), timezone=best.get("timezone"))


def parse_forecast(doc: dict[str, Any], place: Place | None = None, source: str = "open-meteo",
                   fetched_at: float | None = None) -> Weather:
    cur = doc.get("current") or {}
    if not cur:
        raise ValueError("open-meteo response has no 'current' block")

    def f(key: str, default: float | None = None) -> float | None:
        v = cur.get(key)
        try:
            return float(v) if v is not None else default
        except (TypeError, ValueError):
            return default

    return Weather(
        place=place.name if place else "?",
        lat=place.lat if place else float(doc.get("latitude", PRETORIA[0])),
        lon=place.lon if place else float(doc.get("longitude", PRETORIA[1])),
        temp=f("temperature_2m"), feels=f("apparent_temperature"), humidity=f("relative_humidity_2m"),
        is_day=bool(int(cur["is_day"])) if cur.get("is_day") is not None else None,
        precipitation=f("precipitation", 0.0) or 0.0, rain=f("rain", 0.0) or 0.0, showers=f("showers", 0.0) or 0.0,
        code=int(f("weather_code", 0) or 0), cloud_cover=f("cloud_cover", 0.0) or 0.0,
        wind_kmh=f("wind_speed_10m", 0.0) or 0.0, wind_dir=f("wind_direction_10m", 270.0) or 0.0,
        gusts_kmh=f("wind_gusts_10m", 0.0) or 0.0, observed=cur.get("time"),
        fetched_at=fetched_at if fetched_at is not None else time.time(), source=source,
    )


# ───────────────────────────── synthetic weather (demo / forced) ─────────────────────────────

SYNTH = {
    # condition: (code, cloud %, precip mm, temp, wind km/h, wind dir, gusts)
    "clear": (0, 5, 0.0, 24.0, 6.0, 300.0, 14.0),
    "partly": (2, 45, 0.0, 22.0, 11.0, 290.0, 24.0),
    "cloudy": (2, 80, 0.0, 19.0, 14.0, 250.0, 28.0),
    "overcast": (3, 100, 0.0, 17.0, 12.0, 200.0, 25.0),
    "fog": (45, 100, 0.0, 11.0, 2.0, 180.0, 5.0),
    "drizzle": (53, 100, 0.4, 14.0, 9.0, 160.0, 20.0),
    "rain": (63, 100, 2.5, 15.0, 18.0, 140.0, 35.0),
    "heavy": (65, 100, 8.0, 14.0, 26.0, 120.0, 50.0),
    "storm": (95, 100, 6.0, 18.0, 32.0, 100.0, 62.0),
    "snow": (73, 100, 1.0, -1.0, 10.0, 180.0, 20.0),
}
DEMO_CYCLE = ["partly", "clear", "cloudy", "drizzle", "rain", "storm", "heavy", "overcast", "fog"]
DEMO_PERIOD = 40.0


def synthetic(condition: str, place: str = "Pretoria", source: str = "demo", t: float | None = None) -> Weather:
    code, cc, mm, temp, wind, wdir, gust = SYNTH.get(condition, SYNTH["partly"])
    t = time.time() if t is None else t
    wobble = math.sin(t / 23.0)
    return Weather(place=place, temp=temp + wobble, feels=temp - 1 + wobble, humidity=45 + cc * 0.4,
                   precipitation=mm, rain=mm, code=code, cloud_cover=cc, wind_kmh=max(0.0, wind + 3 * wobble),
                   wind_dir=wdir, gusts_kmh=gust, fetched_at=t, source=source)


def demo_condition(t: float, t0: float = 0.0) -> str:
    return DEMO_CYCLE[int((t - t0) // DEMO_PERIOD) % len(DEMO_CYCLE)]


# ───────────────────────────── sun & moon ─────────────────────────────


def sun_position(ts: float, lat: float, lon: float) -> tuple[float, float]:
    """Solar elevation and azimuth (degrees, azimuth clockwise from north) for a unix time."""
    d = ts / 86400.0 + 2440587.5 - 2451545.0
    g = math.radians((357.529 + 0.98560028 * d) % 360)
    q = (280.459 + 0.98564736 * d) % 360
    lam = math.radians((q + 1.915 * math.sin(g) + 0.020 * math.sin(2 * g)) % 360)
    eps = math.radians(23.439 - 0.00000036 * d)
    ra = math.atan2(math.cos(eps) * math.sin(lam), math.cos(lam))
    dec = math.asin(math.sin(eps) * math.sin(lam))
    gmst = (18.697374558 + 24.06570982441908 * d) % 24
    lst = math.radians((gmst * 15 + lon) % 360)
    ha = lst - ra
    la = math.radians(lat)
    elev = math.asin(math.sin(la) * math.sin(dec) + math.cos(la) * math.cos(dec) * math.cos(ha))
    az = math.atan2(-math.sin(ha), math.tan(dec) * math.cos(la) - math.sin(la) * math.cos(ha))
    return math.degrees(elev), math.degrees(az) % 360


SYNODIC = 29.530588853
NEW_MOON_JD = 2451550.26


def moon_phase(ts: float) -> float:
    """0 = new, 0.5 = full, 1 = new again."""
    jd = ts / 86400.0 + 2440587.5
    return ((jd - NEW_MOON_JD) / SYNODIC) % 1.0


def moon_position(ts: float, lat: float, lon: float) -> tuple[float, float]:
    """Rough moon elevation/azimuth: the moon trails the sun by phase x 24 h (good enough for a sky)."""
    lag = moon_phase(ts) * 86400.0 * (SYNODIC / (SYNODIC - 1))
    return sun_position(ts - lag, lat, lon)


# ───────────────────────────── the service ─────────────────────────────


def cache_path() -> Path:
    base = os.environ.get("XDG_CACHE_HOME") or os.path.join(os.path.expanduser("~"), ".cache")
    return Path(base) / "vuurwag" / "weather.json"


def _get_json(url: str, timeout: float = 8.0) -> dict[str, Any]:
    req = urllib.request.Request(url, headers={"User-Agent": "vuurwag/0.2 (+https://open-meteo.com)"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 - fixed https endpoints
        return json.loads(resp.read().decode("utf-8"))


WeatherCallback = Callable[["WeatherService"], Awaitable[None] | None]


class WeatherService:
    """Keeps `current` fresh. mode: live | demo | off. `forced` pins a synthetic condition."""

    def __init__(self, place: str | None = None, mode: str = "live", forced: str | None = None,
                 refresh: float = REFRESH_SECONDS, fetch: Callable[[str], dict[str, Any]] | None = None,
                 cache_file: Path | None = None) -> None:
        self.place_query = place or os.environ.get("VUURWAG_PLACE") or DEFAULT_PLACE
        self.mode = mode
        self.forced = forced if forced and forced != "auto" else None
        self.refresh = refresh
        self.fetch = fetch or _get_json
        self.cache_file = cache_file if cache_file is not None else cache_path()
        self.place: Place | None = None
        self.current: Weather | None = None
        self.last_error: str | None = None
        self.notes: list[str] = []          # one-off log lines for the scene (fallbacks, first fix)
        self.t0 = time.time()
        self._task: asyncio.Task[None] | None = None
        self._load_cache()

    # ── what the scene reads ──
    @property
    def display_name(self) -> str:
        if self.place:
            return self.place.name
        name = split_place(self.place_query)[0]
        return (name.split(",")[0].strip() if name else "") or PRETORIA_LABEL

    @property
    def latlon(self) -> tuple[float, float]:
        if self.place:
            return self.place.lat, self.place.lon
        if self.current and self.current.source in ("open-meteo", "cache"):
            return self.current.lat, self.current.lon
        return PRETORIA

    def weather(self, now: float | None = None) -> Weather | None:
        now = time.time() if now is None else now
        if self.forced:
            w = synthetic(self.forced, self.display_name, "forced", now)
            w.lat, w.lon = self.latlon
            return w
        if self.mode == "demo":
            w = synthetic(demo_condition(now, self.t0), self.display_name, "demo", now)
            w.lat, w.lon = self.latlon
            return w
        if self.mode == "off":
            return None
        if self.current and now - self.current.fetched_at < STALE_SECONDS:
            return self.current
        return None

    @property
    def status(self) -> str:
        if self.forced:
            return "forced"
        if self.mode in ("demo", "off"):
            return self.mode
        if self.current is None:
            return "offline"
        return "ok" if self.current.age < STALE_SECONDS else "offline"

    # ── cache ──
    def _load_cache(self) -> None:
        if self.mode != "live":
            return
        try:
            doc = json.loads(self.cache_file.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return
        if doc.get("query") != self.place_query:
            return
        try:
            if doc.get("place"):
                self.place = Place(**doc["place"])
            if doc.get("weather"):
                w = Weather(**doc["weather"])
                w.source = "cache"
                self.current = w
        except TypeError:
            self.place = None
            self.current = None

    def _save_cache(self) -> None:
        try:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            doc = {"query": self.place_query, "place": asdict(self.place) if self.place else None,
                   "weather": asdict(self.current) if self.current else None}
            self.cache_file.write_text(json.dumps(doc), encoding="utf-8")
        except OSError:
            pass

    # ── network ──
    def fetch_now(self) -> Weather:
        """Blocking fetch (runs in a thread)."""
        if self.place is None:
            place = None
            hint = country_hint(self.place_query)
            for name, cc, fallback in geocode_candidates(self.place_query):
                place = parse_geocode(self.fetch(geocode_url(name, cc)), f"{name}, {cc or hint}" if (cc or hint) else name)
                if place is not None:
                    if fallback:
                        self.notes.append(f"weather: Open-Meteo does not know '{self.place_query}', using {place.name} instead")
                    else:
                        self.notes.append(f"weather: {place.name} ({place.lat:.3f}, {place.lon:.3f}) via Open-Meteo")
                    break
            if place is None:
                raise ValueError(f"place not found: {self.place_query}")
            self.place = place
        doc = self.fetch(forecast_url(self.place.lat, self.place.lon))
        w = parse_forecast(doc, self.place)
        self.current = w
        self.last_error = None
        self._save_cache()
        return w

    async def refresh_once(self) -> Weather | None:
        if self.mode != "live":
            return self.weather()
        try:
            return await asyncio.to_thread(self.fetch_now)
        except Exception as exc:  # noqa: BLE001 - offline is a normal state
            self.last_error = str(exc)[:120]
            return None

    async def run(self, callback: WeatherCallback | None = None) -> None:
        while True:
            if self.mode == "live":
                fresh = self.current is not None and self.current.source == "open-meteo" and self.current.age < self.refresh
                if not fresh:
                    await self.refresh_once()
            if callback:
                res = callback(self)
                if asyncio.iscoroutine(res):
                    await res
            wait = self.refresh if (self.mode == "live" and self.last_error is None) else 60.0
            await asyncio.sleep(wait if self.mode == "live" else 5.0)

    def start(self, callback: WeatherCallback | None = None) -> asyncio.Task[None]:
        self._task = asyncio.create_task(self.run(callback))
        return self._task

    def stop(self) -> None:
        if self._task:
            self._task.cancel()
