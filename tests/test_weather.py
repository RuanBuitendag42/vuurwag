"""Open-Meteo parsing (fixtures are real responses), place fallbacks, caching, offline behaviour, sun and moon."""
from __future__ import annotations

import json
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from vuurwag.weather import (CONDITIONS, DEFAULT_PLACE, PRETORIA, Weather, WeatherService, condition_for,
                             demo_condition, forecast_url, geocode_candidates, geocode_url, moon_phase, parse_forecast,
                             parse_geocode, split_place, sun_position, synthetic)

FIX = Path(__file__).parent / "fixtures"


def load(name: str) -> dict:
    return json.loads((FIX / name).read_text())


def test_parse_real_geocode_and_forecast():
    place = parse_geocode(load("open-meteo-geocode-pierre-van-ryneveld.json"), "Pierre van Ryneveld, ZA")
    assert place is not None and place.name == "Pierre van Ryneveld" and place.country_code == "ZA"
    assert math.isclose(place.lat, -25.838, abs_tol=0.01) and math.isclose(place.lon, 28.245, abs_tol=0.01)
    w = parse_forecast(load("open-meteo-forecast-pierre-van-ryneveld.json"), place)
    assert w.place == "Pierre van Ryneveld" and w.source == "open-meteo"
    assert w.temp == 28.8 and w.humidity == 30 and w.is_day is True
    assert w.code == 1 and w.condition == "clear" and w.label == "Mainly clear"
    assert w.wind_kmh == 9.0 and w.wind_dir == 250 and w.gusts_kmh == 26.3
    assert w.rain_intensity == 0.0
    pta = parse_forecast(load("open-meteo-forecast-pretoria.json"), parse_geocode(load("open-meteo-geocode-pretoria.json"), "Pretoria, ZA"))
    assert pta.place == "Pretoria" and pta.temp is not None


def test_parse_forecast_without_current_block_raises():
    with pytest.raises(ValueError):
        parse_forecast({"latitude": 1})


def test_geocode_picks_the_requested_country():
    doc = {"results": [{"name": "Pretoria", "latitude": 1, "longitude": 2, "country_code": "US"},
                       {"name": "Pretoria", "latitude": -25.7, "longitude": 28.2, "country_code": "ZA"}]}
    assert parse_geocode(doc, "Pretoria, ZA").country_code == "ZA"
    assert parse_geocode({"results": []}, "x") is None


@pytest.mark.parametrize("code,cover,cond", [
    (0, 5, "clear"), (1, 50, "partly"), (1, 90, "cloudy"), (2, 40, "partly"), (3, 100, "overcast"), (45, 100, "fog"),
    (53, 100, "drizzle"), (63, 100, "rain"), (81, 100, "rain"), (65, 100, "heavy"), (82, 100, "heavy"),
    (95, 100, "storm"), (99, 100, "storm"), (73, 100, "snow"),
])
def test_wmo_codes_map_to_conditions(code, cover, cond):
    assert condition_for(code, cover) == cond


def test_place_parsing_and_candidates():
    assert split_place("Pretoria, ZA") == ("Pretoria", "ZA")
    assert split_place("Pierre van Ryneveld, Centurion, South Africa") == ("Pierre van Ryneveld, Centurion", "ZA")
    assert split_place("Lisbon") == ("Lisbon", None)
    cands = geocode_candidates(DEFAULT_PLACE)
    assert ("Pierre van Ryneveld", "ZA", False) in cands
    assert cands[-1] == ("Centurion", "ZA", True)
    assert "countryCode=ZA" in geocode_url("Centurion", "ZA") and "name=Centurion" in geocode_url("Centurion", "ZA")
    assert "current=temperature_2m,relative_humidity_2m" in forecast_url(-25.8, 28.2)


def fake_fetch(table: dict[str, dict]):
    calls = []

    def fetch(url: str) -> dict:
        calls.append(url)
        for key, doc in table.items():
            if key in url:
                return doc
        return {"results": []} if "geocoding" in url else {}
    return fetch, calls


def test_fallback_to_centurion_is_logged(tmp_path):
    centurion = {"results": [{"name": "Centurion", "latitude": -25.86, "longitude": 28.19, "country_code": "ZA"}]}
    fetch, calls = fake_fetch({"name=Centurion": centurion, "api.open-meteo.com": load("open-meteo-forecast-pierre-van-ryneveld.json")})
    svc = WeatherService(place="Nowhere Park, Centurion, South Africa", fetch=fetch, cache_file=tmp_path / "w.json")
    w = svc.fetch_now()
    assert svc.place.name == "Centurion" and w.place == "Centurion"
    assert any("using Centurion" in n for n in svc.notes)
    assert svc.status == "ok" and svc.weather() is w


def test_cache_roundtrip_and_offline(tmp_path):
    fetch, calls = fake_fetch({"geocoding": load("open-meteo-geocode-pierre-van-ryneveld.json"),
                               "api.open-meteo.com": load("open-meteo-forecast-pierre-van-ryneveld.json")})
    cache = tmp_path / "weather.json"
    svc = WeatherService(fetch=fetch, cache_file=cache)
    svc.fetch_now()
    assert cache.exists()
    n = len(calls)

    def offline(url: str) -> dict:
        raise OSError("no network")
    again = WeatherService(fetch=offline, cache_file=cache)   # loads from cache, no network needed
    assert len(calls) == n and again.current is not None and again.current.source == "cache"
    assert again.weather() is not None and again.display_name == "Pierre van Ryneveld"
    again.current.fetched_at -= 7200                          # an old reading is not shown
    assert again.weather() is None and again.status == "offline"
    import asyncio
    assert asyncio.run(again.refresh_once()) is None and "no network" in again.last_error


def test_offline_from_scratch_means_no_weather(tmp_path):
    def offline(url: str) -> dict:
        raise OSError("down")
    svc = WeatherService(fetch=offline, cache_file=tmp_path / "none.json")
    assert svc.weather() is None and svc.status == "offline" and svc.latlon == PRETORIA
    off = WeatherService(mode="off", cache_file=tmp_path / "none.json")
    assert off.weather() is None and off.status == "off"


def test_demo_cycles_and_forced(tmp_path):
    seen = {demo_condition(t * 40.0) for t in range(12)}
    assert {"clear", "rain", "storm", "fog"} <= seen
    demo = WeatherService(mode="demo", cache_file=tmp_path / "x.json")
    assert demo.weather().source == "demo" and demo.status == "demo"
    forced = WeatherService(mode="live", forced="storm", cache_file=tmp_path / "x.json")
    w = forced.weather()
    assert w.condition == "storm" and w.rain_intensity > 0.5 and forced.status == "forced"
    for c in CONDITIONS:
        assert synthetic(c).condition == c


def test_wind_points_downwind_on_screen():
    # the camera faces west-north-west; a westerly blows towards the viewer's right-ish (east)
    w = Weather(wind_kmh=20, wind_dir=270)
    assert w.wind_x > 0
    east = Weather(wind_kmh=20, wind_dir=90)
    assert math.copysign(1, east.wind_x) == -math.copysign(1, w.wind_x)


def test_sun_and_moon():
    lat, lon = PRETORIA
    sast = timezone(timedelta(hours=2))
    noon = datetime(2026, 10, 9, 12, 0, tzinfo=sast).timestamp()
    midnight = datetime(2026, 10, 9, 0, 0, tzinfo=sast).timestamp()
    assert sun_position(noon, lat, lon)[0] > 60
    assert sun_position(midnight, lat, lon)[0] < -30
    evening = sun_position(datetime(2026, 10, 9, 18, 0, tzinfo=sast).timestamp(), lat, lon)
    assert -3 < evening[0] < 5 and 250 < evening[1] < 290    # setting in the west
    assert all(0 <= moon_phase(noon + d * 86400) < 1 for d in range(30))
