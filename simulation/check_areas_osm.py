"""Compare the hand-typed area coordinates with OpenStreetMap (Nominatim).

The 50 area centres in ``areas.py`` were typed by hand. This script asks the public
OpenStreetMap geocoder for each area name and prints how far its answer is from our
coordinates, so the team can review the differences and cite OpenStreetMap (ODbL).

Usage (needs internet; one request per second, as the Nominatim usage policy asks)::

    python -m simulation.check_areas_osm                # prints a table
    python -m simulation.check_areas_osm --threshold 2  # flag areas more than 2 km apart

It never changes ``areas.py``: a geocoder can return the wrong place for a common name,
so a person must read the table and update the coordinates by hand. Names that
the geocoder does not know (for example "Badya University area") show as "not found".
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.parse
import urllib.request

from simulation.areas import AREAS
from simulation.generate import haversine_km

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "wnesny-student-project (Badya University coursework)"


def parse_result(payload: str) -> tuple[float, float] | None:
    """Return (latitude, longitude) of the first Nominatim result, or None if there is none."""
    data = json.loads(payload)
    if not data:
        return None
    return float(data[0]["lat"]), float(data[0]["lon"])


# Greater Cairo (west, north, east, south). Searching only inside this box stops the geocoder from returning
# a place with the same name far away (the first run matched "Haram" to a place 54 km away).
GREATER_CAIRO_VIEWBOX = "30.85,30.35,31.85,29.75"


def fetch_osm_point(name: str) -> tuple[float, float] | None:
    query = urllib.parse.urlencode(
        {
            "q": name,
            "format": "json",
            "limit": 1,
            "countrycodes": "eg",
            "viewbox": GREATER_CAIRO_VIEWBOX,
            "bounded": 1,
        }
    )
    request = urllib.request.Request(f"{NOMINATIM_URL}?{query}", headers={"User-Agent": USER_AGENT})
    last_error: Exception | None = None
    for attempt in range(3):  # a slow or busy service gets two more tries, with a growing pause
        try:
            with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310 (fixed https URL)
                return parse_result(response.read().decode("utf-8"))
        except OSError as exc:  # URLError and timeouts are OSError subclasses
            last_error = exc
            time.sleep(2 * (attempt + 1))
    raise ConnectionError(f"OpenStreetMap did not answer for {name!r}: {last_error}")


def compare(fetch=fetch_osm_point, pause: float = 1.0) -> list[dict]:
    """One row per area: our point, the OpenStreetMap point and the distance between them in km."""
    rows = []
    for name, zone, lat, lon, _popularity in AREAS:
        try:
            point, error = fetch(name), None
        except ConnectionError as exc:
            point, error = None, str(exc)
        rows.append(
            {
                "name": name,
                "zone": zone,
                "lat": lat,
                "lon": lon,
                "osm": point,
                "km": None if point is None else float(haversine_km(lat, lon, point[0], point[1])),
                "error": error,
            }
        )
        if pause:
            time.sleep(pause)
    return rows


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--threshold", type=float, default=3.0, help="flag areas farther than this many km (default 3)")
    args = parser.parse_args(argv)
    flagged = 0
    print(f"{'area':28} {'our lat,lon':22} {'OSM lat,lon':22} {'km':>6}")
    for row in compare():
        ours = f"{row['lat']:.4f},{row['lon']:.4f}"
        if row["osm"] is None:
            label = "no answer" if row["error"] else "not found"
            print(f"{row['name']:28} {ours:22} {label:22} {'':>6}  CHECK")
            flagged += 1
            continue
        osm = f"{row['osm'][0]:.4f},{row['osm'][1]:.4f}"
        mark = "  CHECK" if row["km"] > args.threshold else ""
        flagged += bool(mark)
        print(f"{row['name']:28} {ours:22} {osm:22} {row['km']:6.1f}{mark}")
    print(f"\n{flagged} area(s) to review (\"no answer\" means the service timed out: run the script again later). Data (c) OpenStreetMap contributors, ODbL.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
