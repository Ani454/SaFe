"""Phase 3: search + stats for "Ask about my block" (index: sf311)."""
import os

import requests
from dotenv import load_dotenv
from elasticsearch import Elasticsearch

load_dotenv()

INDEX = "sf311"
es = Elasticsearch(os.environ["ES_URL"], api_key=os.environ["ES_API_KEY"])

SOURCE_FIELDS = [
    "service_request_id", "requested_datetime", "closed_date",
    "status_description", "service_name", "service_subtype",
    "analysis_neighborhood", "address", "status_notes",
    "resolution_hours", "location",
]


def list_neighborhoods():
    """Dropdown values, A-Z."""
    resp = es.search(
        index=INDEX,
        size=0,
        aggs={"hoods": {"terms": {
            "field": "analysis_neighborhood", "size": 100, "order": {"_key": "asc"},
        }}},
    )
    return [b["key"] for b in resp["aggregations"]["hoods"]["buckets"]]


def get_neighborhood_stats(neighborhood, days=30, map_size=300):
    flt = {"term": {"analysis_neighborhood": neighborhood}}
    return _run_stats(flt, days, map_size, scope={"type": "neighborhood", "name": neighborhood})


def get_block_stats(lat, lon, radius="500m", days=30, map_size=300):
    flt = {"geo_distance": {"distance": radius, "location": {"lat": lat, "lon": lon}}}
    return _run_stats(flt, days, map_size,
                      scope={"type": "radius", "lat": lat, "lon": lon, "radius": radius})


def _run_stats(area_filter, days, map_size, scope):
    resp = es.search(
        index=INDEX,
        size=map_size,                 # newest N: first 5 = examples, all = map points
        track_total_hits=True,         # real total, not capped at 10,000
        source_includes=SOURCE_FIELDS,
        sort=[{"requested_datetime": "desc"}],
        query={"bool": {"filter": [
            area_filter,
            {"range": {"requested_datetime": {"gte": f"now-{days}d/d"}}},
        ]}},
        aggs={
            "top_issues": {"terms": {"field": "service_name", "size": 5}},
            "status": {"terms": {"field": "status_description", "size": 10}},
            "fix_time": {"percentiles": {"field": "resolution_hours", "percents": [50, 90]}},
        },
    )
    return _shape(resp, scope, days)


def _short_address(addr):
    # "9 OLIVE ST, Virtual, SAN FRANCISCO, CA 94109, US" -> "9 Olive St"
    return (addr or "").split(",")[0].strip().title()


def _round(x, n=1):
    return None if x is None else round(x, n)


def _shape(resp, scope, days):
    aggs = resp["aggregations"]
    total = resp["hits"]["total"]["value"]
    status = {b["key"]: b["doc_count"] for b in aggs["status"]["buckets"]}
    closed = status.get("Closed", 0)
    pct = aggs["fix_time"]["values"]
    median_h = pct.get("50.0")
    p90_h = pct.get("90.0")
    hits = [h["_source"] for h in resp["hits"]["hits"]]

    return {
        "scope": scope,
        "window_days": days,
        "total_cases": total,
        "open": status.get("Open", 0),
        "closed": closed,
        "status_breakdown": status,
        "pct_closed": _round(100 * closed / total) if total else None,
        # Computed over CLOSED cases only (open cases have no resolution_hours).
        "median_hours_to_fix": _round(median_h),
        "median_days_to_fix": _round(median_h / 24) if median_h is not None else None,
        "p90_hours_to_fix": _round(p90_h),
        "top_issues": [
            {"issue": b["key"], "count": b["doc_count"]}
            for b in aggs["top_issues"]["buckets"]
        ],
        "recent_cases": [
            {
                "requested": h.get("requested_datetime"),
                "issue": h.get("service_name"),
                "subtype": h.get("service_subtype"),
                "status": h.get("status_description"),
                "address": _short_address(h.get("address")),
                "notes": h.get("status_notes"),
            }
            for h in hits[:5]
        ],
        "map_points": [
            {"lat": h["location"]["lat"], "lon": h["location"]["lon"]}
            for h in hits if h.get("location")
        ],
    }


def for_llm(stats):
    """Stats minus the map points -- what you send to Mistral in Phase 4."""
    return {k: v for k, v in stats.items() if k != "map_points"}


def geocode(address):
    """Optional: typed address -> (lat, lon) via Nominatim, bounded to SF. None if not found."""
    resp = requests.get(
        "https://nominatim.openstreetmap.org/search",
        params={
            "q": f"{address}, San Francisco, CA",
            "format": "json",
            "limit": 1,
            "viewbox": "-122.52,37.83,-122.35,37.70",
            "bounded": 1,
        },
        headers={"User-Agent": "ask-about-my-block-demo"},
        timeout=10,
    )
    resp.raise_for_status()
    results = resp.json()
    if not results:
        return None
    return float(results[0]["lat"]), float(results[0]["lon"])