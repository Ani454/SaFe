"""Run Phase 4 on three very different neighborhoods plus one radius search."""
import json
import time

from summarize import build_payload, summarize_block, check_numbers
from stats import get_block_stats, get_neighborhood_stats

DAYS = 30
runs = [(name, get_neighborhood_stats(name, days=DAYS))
        for name in ["Tenderloin", "Mission", "Sunset/Parkside"]]
runs.append(("500 m around 9 Olive St", get_block_stats(37.78459683, -122.41803808, days=DAYS)))

results = []
for label, s in runs:
    payload = build_payload(s, area_label=label, days=DAYS)
    summary = summarize_block(payload)
    flagged = check_numbers(summary, payload)

    print(f"\n===== {label} =====")
    print(summary)
    print("Numbers not in data:", flagged or "none")
    results.append({"area": label, "payload": payload, "summary": summary, "flagged": flagged})
    time.sleep(2)  # stay under the free-tier rate limit

with open("phase4_test_run.json", "w") as f:
    json.dump(results, f, indent=2, default=str)