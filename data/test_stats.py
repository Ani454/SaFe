import json
import time

from stats import (for_llm, geocode, get_block_stats,
                   get_neighborhood_stats, list_neighborhoods)

hoods = list_neighborhoods()
print(f"{len(hoods)} neighborhoods (expect 41):", hoods[:5], "...")


def check(label, s):
    print(f"\n=== {label} ===")
    print(json.dumps(for_llm(s), indent=2, default=str))
    print("map points:", len(s["map_points"]))
    if s["open"] + s["closed"] != s["total_cases"]:
        print("!! open + closed != total -> other statuses:", s["status_breakdown"])


for name in ["Tenderloin", "Mission", "Sunset/Parkside"]:
    check(f"Neighborhood: {name}", get_neighborhood_stats(name, days=30))

# 500 m around 9 Olive St (from your sample hit)
for r in ["250m", "500m", "1km"]:
    s = get_block_stats(37.78459683, -122.41803808, radius=r, days=30)
    print(f"\nRadius {r}: {s['total_cases']} cases")
check("Radius 500m @ 9 Olive St", get_block_stats(37.78459683, -122.41803808))

# Optional geocode test
time.sleep(1)  # Nominatim: max 1 req/sec
coords = geocode("729 Larkin St")
print("\nGeocode 729 Larkin St ->", coords, "(expect ~37.7846, -122.4179)")
if coords:
    check("Geocoded 729 Larkin St", get_block_stats(*coords))

print(get_neighborhood_stats("Tenderloin", map_size=10))