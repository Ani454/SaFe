"""Phase 4: turn get_block_stats() / get_neighborhood_stats() output into a Mistral summary.

Works on the processed dict that Phase 3 returns (total_cases, open, closed, status_breakdown,
map_points, ...), using stats.for_llm() to get the model-ready version.
"""
import json
import os
import re
import time

from dotenv import load_dotenv
from mistralai.client import Mistral

load_dotenv()
client = Mistral(api_key=os.environ["MISTRAL_API_KEY"])
# mistral-small-latest is rate limited on this account; ministral-8b-latest works.
# Override with MISTRAL_MODELS=model1,model2 in .env. Tried in order.
MODELS = [m.strip() for m in os.getenv("MISTRAL_MODELS", "ministral-8b-latest,mistral-small-latest").split(",") if m.strip()]

SYSTEM_PROMPT = """You explain San Francisco 311 data to residents.

Rules:
- Use only the numbers in the STATS JSON. Do not calculate, estimate, or re-round anything.
- If a value is null, say that data isn't available. Never guess.
- Write 4-6 sentences of plain prose. No bullet points, no headings.
- Cover: what gets reported most, how fast issues get fixed (median days), and one notable thing
  (for example a high share of open cases, or something unusual in the recent examples).
- The sample cases are only examples. Don't count them or treat them as typical.
- Don't comment on safety, crime, rent, or property values.
- Give times only in days, exactly as written in the data. Never mention hours.
- Plain text only: no bold, no markdown.
- Describe what the data shows; don't guess at causes (avoid "suggesting...", "likely because...").
- Quote percentages and numbers exactly as given. Never round them or turn them into words or fractions ("about", "nearly three-quarters", "half").
- Don't compare open and closed percentages to each other."""


# ---------- Step 1: build the payload from the Phase 3 output ----------

from stats import for_llm


def build_payload(s, area_label, days):
    payload = dict(for_llm(s))
    payload["area"] = area_label

    # Hours confuse the model. Give it days only, as a ready-made phrase.
    payload.pop("median_hours_to_fix", None)
    p90_h = payload.pop("p90_hours_to_fix", None)
    if p90_h is not None:
        payload["slowest_cases"] = (
            f"The slowest 10% of closed cases took more than {round(p90_h / 24, 1)} days"
        )

    # Pre-compute the open share so the model doesn't do 100 - pct_closed itself
    if payload.get("pct_closed") is not None:
        payload["pct_open"] = round(100 - payload["pct_closed"], 1)
    

    if payload.get("median_days_to_fix") is not None:
        payload["typical_fix"] = f"Half of closed cases were fixed within {payload['median_days_to_fix']} days"

    return payload


# ---------- Step 2: call Mistral ----------

def _is_rate_limit(err):
    status = getattr(err, "status_code", None) or getattr(getattr(err, "raw_response", None), "status_code", None)
    return status == 429 or "429" in str(err) or "rate_limited" in str(err)


def call_mistral(messages, temperature=0.2, json_mode=False, max_retries=3):
    """Try each model in MODELS; on a 429, back off briefly, then move to the next model."""
    kwargs = {"response_format": {"type": "json_object"}} if json_mode else {}
    last_err = None
    for model in MODELS:
        wait = 2
        for attempt in range(max_retries + 1):
            try:
                resp = client.chat.complete(model=model, messages=messages,
                                            temperature=temperature, **kwargs)
                return resp.choices[0].message.content.strip()
            except Exception as err:
                if not _is_rate_limit(err):
                    raise
                last_err = err
                if attempt < max_retries:
                    print(f"{model} rate limited, retrying in {wait}s ({attempt + 1}/{max_retries})")
                    time.sleep(wait)
                    wait = min(wait * 2, 30)
        print(f"{model} still rate limited, trying next model")
    raise last_err


def summarize_block(payload):
    if not payload.get("total_cases"):
        # Don't spend an API call (or risk a made-up answer) when there's nothing to explain.
        return (f"There were no 311 cases recorded for {payload['area']} "
                f"in the last {payload['period_days']} days.")

    user_msg = "STATS JSON:\n" + json.dumps(payload, indent=2, default=str) + "\n\nWrite the summary."
    return call_mistral([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_msg},
    ])


# ---------- Step 3: catch made-up numbers ----------

def _numbers_in(obj, out):
    if isinstance(obj, dict):
        for v in obj.values():
            _numbers_in(v, out)
    elif isinstance(obj, list):
        for v in obj:
            _numbers_in(v, out)
    elif isinstance(obj, (int, float)) and not isinstance(obj, bool):
        out.add(float(obj))
    elif isinstance(obj, str):
        for n in re.findall(r"\d+(?:\.\d+)?", obj):
            out.add(float(n))
    return out


def check_numbers(summary, payload):
    """Return numbers in the summary that don't appear anywhere in the payload."""
    allowed = _numbers_in(json.loads(json.dumps(payload, default=str)), set()) | {311.0}
    found = re.findall(r"\d[\d,]*(?:\.\d+)?", summary)
    return [n for n in found if float(n.replace(",", "")) not in allowed]


# ---------- Step 4 (stretch): follow-up questions like "what about graffiti?" ----------

def pick_service(question, available_services):
    """Ask Mistral to map a free-text question to one exact service_name, or null."""
    prompt = (
        "Map the user's question to ONE service name from this list, or null if none fits.\n"
        f"Services: {json.dumps(available_services)}\n"
        f"Question: {question}\n"
        'Reply as JSON: {"service_name": <exact name from the list or null>}'
    )
    raw = call_mistral([{"role": "user", "content": prompt}], temperature=0, json_mode=True)
    try:
        name = json.loads(raw).get("service_name")
    except json.JSONDecodeError:
        return None
    return name if name in available_services else None  # never trust a name not in the list


def answer_followup(question, payload, available_services, rerun_stats):
    """rerun_stats(service_name) -> fresh payload filtered to that service."""
    service = pick_service(question, available_services)
    stats = rerun_stats(service) if service else payload

    user_msg = (
        "STATS JSON:\n" + json.dumps(stats, indent=2, default=str)
        + f"\n\nResident's question: {question}\n"
        + "Answer in 2-4 sentences using only these numbers. "
        + "If the data doesn't answer the question, say so."
    )
    return call_mistral([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_msg},
    ])