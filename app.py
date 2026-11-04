"""
Ask about my block - drop a pin on a map of SF and see 311 issues around it.

Run:  streamlit run app.py
Needs: .env with ES_URL, ES_API_KEY, MISTRAL_API_KEY
       sf311 index from Phase 2 (location = geo_point)
"""
import json
import os
from datetime import datetime, timezone

import folium
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from elasticsearch import Elasticsearch
from folium.plugins import HeatMap
from mistralai.client import Mistral
from streamlit_folium import st_folium

load_dotenv()

INDEX = "sf311"
SF_CENTER = [37.7749, -122.4194]
MODEL ="ministral-8b-latest"

SYSTEM_PROMPT = (
    "You explain San Francisco 311 data to someone thinking about renting near a spot. "
    "Use only the numbers and cases provided. Write 4-6 sentences: what is reported most, "
    "how fast issues get fixed, and anything in the data that would affect day-to-day "
    "life on this block. Mention whichever issues the data shows; don't assume or add any. "
    "No made-up figures. If there are fewer than 10 cases, say the sample is small."
)

st.set_page_config(page_title="Ask about my block", layout="wide")


# ---------- Clients ----------
@st.cache_resource
def get_clients():
    es = Elasticsearch(os.environ["ES_URL"], api_key=os.environ["ES_API_KEY"])
    mistral = Mistral(api_key=os.environ["MISTRAL_API_KEY"])
    return es, mistral


es, mistral = get_clients()


# ---------- Data ----------
@st.cache_data(ttl=3600, show_spinner=False)
def latest_case_millis() -> int:
    """Newest requested_datetime in the index. Date windows are measured back
    from this, so a snapshot pulled weeks ago still returns results."""
    resp = es.search(
        index=INDEX,
        size=0,
        aggs={"latest": {"max": {"field": "requested_datetime"}}},
    )
    return int(resp["aggregations"]["latest"]["value"])


@st.cache_data(ttl=600, show_spinner=False)
def get_block_stats(lat: float, lon: float, radius_m: int = 500, days: int = 30,
                    map_points: int = 300) -> dict:
    end = latest_case_millis()
    start = end - days * 86_400_000

    query = {
        "bool": {
            "filter": [
                {"geo_distance": {"distance": f"{radius_m}m",
                                  "location": {"lat": lat, "lon": lon}}},
                {"range": {"requested_datetime": {"gte": start, "lte": end,
                                                  "format": "epoch_millis"}}},
            ]
        }
    }

    resp = es.search(
        index=INDEX,
        query=query,
        size=map_points,
        sort=[{"requested_datetime": "desc"}],
        source=["service_name", "service_subtype", "status_description",
                "requested_datetime", "address", "status_notes", "location"],
        aggs={
            "top_issues": {"terms": {"field": "service_name", "size": 5}},
            "status": {"terms": {"field": "status_description"}},
            "median_fix": {"percentiles": {"field": "resolution_hours",
                                           "percents": [50]}},
        },
        track_total_hits=True,
    )

    total = resp["hits"]["total"]["value"]
    aggs = resp["aggregations"]

    status_counts = {b["key"]: b["doc_count"] for b in aggs["status"]["buckets"]}
    closed = sum(v for k, v in status_counts.items() if k.lower() == "closed")
    median_hours = aggs["median_fix"]["values"].get("50.0")

    cases = [h["_source"] for h in resp["hits"]["hits"]]

    return {
        "radius_m": radius_m,
        "days": days,
        "window_end": datetime.fromtimestamp(end / 1000, tz=timezone.utc).strftime("%Y-%m-%d"),
        "total_cases": total,
        "pct_closed": round(100 * closed / total, 1) if total else None,
        "median_days_to_fix": round(median_hours / 24, 1) if median_hours else None,
        "top_issues": [{"issue": b["key"], "count": b["doc_count"]}
                       for b in aggs["top_issues"]["buckets"]],
        "status_counts": status_counts,
        "recent_cases": cases[:5],
        "map_cases": cases,
    }


@st.cache_data(ttl=600, show_spinner=False)
def summarize(payload_json: str) -> str:
    resp = mistral.chat.complete(
        model=MODEL,
        temperature=0.2,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": payload_json},
        ],
    )
    return resp.choices[0].message.content


# ---------- Sidebar ----------
st.sidebar.header("Search area")
radius_m = st.sidebar.select_slider("Radius", options=[250, 500, 1000], value=500,
                                    format_func=lambda m: f"{m} m")
days = st.sidebar.slider("Days of history", min_value=7, max_value=90, value=30)
layer = st.sidebar.radio("Show cases as", ["Heatmap", "Points"])

if st.sidebar.button("Clear pin"):
    st.session_state.pop("pin", None)
    st.session_state.pop("result", None)
    st.rerun()


# ---------- Map ----------
st.title("Ask about my block")
st.caption("Click the map where you're thinking of renting, then select Explain this spot.")

pin = st.session_state.get("pin")
result = st.session_state.get("result")

m = folium.Map(location=list(pin) if pin else SF_CENTER,
               zoom_start=16 if pin else 13, tiles="OpenStreetMap")

if pin:
    folium.Marker(list(pin), tooltip="Your spot").add_to(m)
    folium.Circle(list(pin), radius=radius_m, color="#2563eb",
                  fill=True, fill_opacity=0.08).add_to(m)

# Only draw cases if they belong to the current pin and settings
if result and result["key"] == (pin, radius_m, days):
    cases = result["stats"]["map_cases"]
    coords = [(c["location"]["lat"], c["location"]["lon"]) for c in cases if c.get("location")]
    if layer == "Heatmap" and coords:
        HeatMap(coords, radius=14, blur=18).add_to(m)
    else:
        for c in cases:
            loc = c.get("location")
            if not loc:
                continue
            is_open = str(c.get("status_description", "")).lower() != "closed"
            folium.CircleMarker(
                [loc["lat"], loc["lon"]], radius=4,
                color="#dc2626" if is_open else "#6b7280",
                fill=True, fill_opacity=0.8,
                tooltip=f'{c.get("service_name")} ({c.get("status_description")})',
            ).add_to(m)

left, right = st.columns([3, 2])

with left:
    out = st_folium(m, height=560, key="map", returned_objects=["last_clicked"])

if out and out.get("last_clicked"):
    click = (round(out["last_clicked"]["lat"], 5), round(out["last_clicked"]["lng"], 5))
    if click != pin:
        st.session_state.pin = click
        st.session_state.pop("result", None)
        st.rerun()


# ---------- Results ----------
with right:
    if not pin:
        st.info("Click anywhere in San Francisco to drop a pin.")
    else:
        st.write(f"Pin at {pin[0]}, {pin[1]}, radius {radius_m} m, last {days} days")
        if st.button("Explain this spot", type="primary"):
            with st.spinner("Pulling 311 cases"):
                stats = get_block_stats(pin[0], pin[1], radius_m, days)
            summary = None
            if stats["total_cases"] > 0:
                payload = {k: v for k, v in stats.items() if k != "map_cases"}
                with st.spinner("Writing summary"):
                    summary = summarize(json.dumps(payload, default=str))
            st.session_state.result = {"key": (pin, radius_m, days),
                                       "stats": stats, "summary": summary}
            st.rerun()

        if result and result["key"] == (pin, radius_m, days):
            stats = result["stats"]
            if stats["total_cases"] == 0:
                st.warning("No 311 cases here in this window. Try a bigger radius, "
                           "more days, or a pin inside San Francisco.")
            else:
                st.subheader("What's going on here")
                st.write(result["summary"])

                c1, c2, c3 = st.columns(3)
                c1.metric("Total cases", stats["total_cases"])
                c2.metric("Closed", f'{stats["pct_closed"]}%' if stats["pct_closed"] is not None else "n/a")
                c3.metric("Median days to fix",
                          stats["median_days_to_fix"] if stats["median_days_to_fix"] is not None else "n/a")

                st.subheader("Top issues")
                st.bar_chart(pd.DataFrame(stats["top_issues"]).set_index("issue"))

                st.subheader("Most recent cases")
                recent = pd.DataFrame(stats["recent_cases"])
                cols = [c for c in ["requested_datetime", "service_name",
                                    "status_description", "address"] if c in recent]
                st.dataframe(recent[cols], hide_index=True, use_container_width=True)

                st.caption(f'Data window ends {stats["window_end"]}. Source: DataSF 311 Cases.')