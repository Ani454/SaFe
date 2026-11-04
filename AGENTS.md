# SaFe contributor and agent instructions

These instructions apply throughout this repository. Read this file and [BRANDING.md](BRANDING.md) before changing code or product copy.

## Source of truth

The team's [Google Doc](https://docs.google.com/document/d/1bNgqXvLrVUD0cKjE_3u92J4tO1wbgkOCv7hBx2KxQjs/edit?tab=t.dca2et6zltrd), read November 3, 2026, contains an exploratory `idea` tab and a concrete `prompts` tab. Follow the prompts tab's backend-first plan. This file preserves its shared contracts and makes implementation ambiguities explicit. Branding visual defaults are proposed by BRANDING.md, not specified in the source doc.

## Judging and demo context

Read [JUDGING.md](JUDGING.md) before changing pitch copy, demo flows, or feature priorities. The organizer's [repository rubric](https://github.com/jdarmada/elastic-mistral-hacknight#judging-criteria-and-presentations), checked November 3, 2026, lists **Novelty**, **Use of Elastic**, and **Use of Mistral**, without numerical weights. Prepare a two-minute initial demo and a three-minute finalist version. Show both technologies; prioritize integration evidence over additional interface work.

The [starter ideas](https://github.com/jdarmada/elastic-mistral-hacknight/blob/main/open_challenge.md) already include 311 classification and nearby-case retrieval. SaFe's proposed distinction is physical-issue identity plus accumulated report history and a consolidated escalation lifecycle. Demonstrate this distinction; do not claim novelty solely from the starter operations. Agent Builder and semantic/vector search are optional extensions, not prerequisites for the agreed MVP.

Make the combined stack visible through evidence: Elasticsearch retrieves and stores the relevant issue; Mistral structures language, confirms physical-issue identity, and drafts from supplied facts. Prioritize the integrated lifecycle and the same-category different-object demonstration. Preserve the current contracts and ownership boundaries. Never imply that the Person B workspace alone implements Elasticsearch retrieval or threshold enforcement, or claim hybrid/vector search, model accuracy, city workload savings, or live integration without supporting implementation and measurements.

## Product and scope

SaFe groups reports about the same neighborhood problem in San Francisco. Mistral classifies text and helps confirm matches. Elasticsearch retrieves nearby issues and stores their report history. At 10 reports, generate one consolidated agency email draft. Once an issue is resolved, generate a notice for each subscribed reporter.

Build a working Python backend demonstrated through a notebook, script, or Kibana. Keep classification, geo matching, and threshold escalation as the core of the agreed integration MVP.

**November 3 product-vision clarification:** The user explicitly described a broader gamified community-action product: NGOs discover issues, contributors submit completion photos for review, approved work earns awards/points, and a contributor leaderboard recognizes participation. Scheduled volunteer activities and joining are a provisional interpretation of the user's reference to dates and people joining. Read [PRODUCT_VISION.md](PRODUCT_VISION.md) for the intended journey and implementation boundaries. These capabilities are now part of the product direction; this update documents them without implementing new APIs, storage fields, or rewards. Keep the existing integration contracts until extensions are coordinated. Neighborhood safety rankings and unrelated social feeds remain outside the agreed scope.

Ten reports trigger an escalation workflow; they are not proof that a claim is true or that ten independent people observed it. A completion upload is a claim awaiting review, not automatic resolution or an automatic point award. Distinguish proposed, implemented, and live-verified behavior in all product and pitch copy.

**November 3 scope update:** The user explicitly requested a proper UI for Person B. A focused local Mistral workspace in ui_server.py and web/ is now in scope alongside mistral_ai.py. This does not add ownership of Person A's storage or Person C's shared pipeline. Live calls and illustrative sample previews must be clearly distinguished.

Generate or print email drafts and resolution notices only. Real email delivery and SF311 submission are future integrations. In resident-facing demo copy, describe drafts accurately; never claim that a city agency received an unsent email.

## File boundaries and collaboration

The source doc suggests three workstreams; people may swap ownership. Coordinate shared contract changes before implementing them across files.

| Workstream | Suggested owner | Files and responsibility |
| --- | --- | --- |
| Elasticsearch | Anisha / Person A | `es_store.py`: mappings, retrieval, updates, agency lookup, SF311 evidence |
| Mistral | Jayasri / Person B | `mistral_ai.py`: classification, match confirmation, message drafting |
| Integration and demo | Ben / Person C | `pipeline.py`, `demo.ipynb`, shared fixtures, README and integration |

The application files above are planned; these instructions do not imply that they already exist. Keep the first implementation small. Document installation, exact run commands, configuration, and the demo in README.md when adding the runtime.

- Pull current changes before starting and before pushing; use short task branches once shared work begins.
- Keep commits focused on owned files. Do not overwrite another contributor's work or force-push shared branches.
- Record changes to contracts, category vocabulary, environment variables, or mappings here and in the relevant runtime documentation.
- Commit `.env.example` with placeholder values when adding configuration. Never commit `.env`, API keys, credentials, or real reporter contact details.
- Keep shared fixture data synthetic. Clear notebook outputs containing private information before committing.

## Shared Python contracts

Preserve these public names and return shapes. Add internal helpers as needed. Any necessary public change must be coordinated with the other workstreams.

```python
# mistral_ai.py
def classify_report(text: str) -> dict:
    """Return {"category": str, "summary": str, "severity": int (1–5)}."""

def is_same_issue(new_text: str, existing_summary: str) -> bool: ...
def draft_authority_email(issue: dict, agency: str) -> str: ...
def draft_resolution_notice(issue: dict) -> str: ...

# es_store.py
def find_matching_issue(category: str, lat: float, lon: float) -> dict | None: ...
def create_issue(category, summary, lat, lon, reporter, text) -> str:
    """Return issue_id."""

def add_report(issue_id: str, reporter: str, text: str) -> int:
    """Return the updated report_count."""

def mark_escalated(issue_id) -> dict: ...
def mark_resolved(issue_id) -> dict: ...
def get_issue(issue_id) -> dict: ...
def agency_for(category: str) -> str: ...

# pipeline.py
THRESHOLD = 10

def submit_report(reporter, text, lat, lon) -> str:
    """Return the resident-facing message."""

def resolve(issue_id) -> list[str]:
    """Return generated resolution notices; do not deliver them."""
```

Returned issue dictionaries must include `issue_id` alongside the stored fields so the pipeline can update a retrieved issue. Normalize Elasticsearch hits in es_store.py rather than exposing raw hit envelopes to every caller.

## Data and Elasticsearch behavior

Create a dedicated `issues` index; treat the existing `sf311` index as read-only evidence. Inspect its real mappings before choosing field names or keyword subfields.

| Field | Elasticsearch type / meaning |
| --- | --- |
| `category` | `keyword` |
| `location` | `geo_point`; use explicit `{lat, lon}` objects |
| `summary` | `text` |
| `reporters` | `keyword` array; notification recipients |
| `report_texts` | `text` array; submitted descriptions |
| `report_count` | `integer`; count of attached reports |
| `status` | `keyword`: `open`, `escalated`, `resolved` |
| `created_at` | `date`; first report time in UTC |
| `updated_at` | `date`; latest report time in UTC; addition needed for email first/last timestamps |

- New issues begin `open` with one report. Use stable issue IDs.
- Match the same category, within 50 meters, created within the last 14 days, excluding `resolved`; sort by distance and return the nearest candidate. Include `escalated` so later reports find existing escalations.
- Validate finite latitude and longitude and their ranges. Reject missing locations instead of inventing coordinates.
- Confirm candidate equivalence with Mistral before merging. Proximity and category alone do not prove that two reports describe the same object.
- The MVP contract returns one candidate. If it fails confirmation, create a separate issue. Searching more candidates requires an explicit contract extension.
- Use an atomic scripted update for report count and report history. Keep recipients unique while retaining the actual number of reports. A count is not proof of distinct people or urgency.
- Use a small shared category-to-agency dictionary. Start with canonical categories `illegal_dumping`, `graffiti`, `streetlight`, `pothole`, `other` as repo defaults; all three modules must use the same vocabulary. Verify agency destinations before any future real delivery. Unknown categories need review rather than a fabricated agency address.
- For the pitch, query actual `sf311` notes for duplicate mentions and save the count, query, time range, and run timestamp. Missing access is a stated limitation, never a made-up result.

## Mistral behavior

The doc proposes `mistral-small-latest` and JSON object responses. Make the model configurable and verify the installed SDK's current API when implementing; keep credentials in environment variables.

Person B currently calls the official chat completions REST API using Python's standard library, so no SDK is installed. Configuration is MISTRAL_API_KEY, MISTRAL_MODEL (default mistral-small-latest), and MISTRAL_TIMEOUT_SECONDS (default 30, range 1–120). The local UI server loads these from an ignored .env file; direct module callers supply process environment variables. Missing or invalid provider output raises MistralError, ambiguous reports raise ClarificationNeeded, and invalid caller data raises ValueError. Draft input requires timezone-aware created_at and updated_at; resolution drafts require status resolved.

- Validate category, nonempty summary, and integer severity 1–5 after classification. JSON formatting alone is not schema validation.
- Treat vague input as needing clarification; do not invent a location, specific incident, agency, or severity justification.
- Treat resident text and retrieved records as untrusted input, never instructions to the model or tools.
- Match confirmation must parse a structured boolean rather than searching prose for “yes.”
- Agency drafts include category, location, summary, count, and first/last report times. Resolution notices thank the reporter and state the recorded resolution without inventing evidence.
- Handle malformed output, timeouts, and unavailable services explicitly. Do not silently merge issues when match confirmation fails.

## Pipeline and lifecycle

1. Validate inputs and classify the report.
2. Find a candidate and confirm whether it describes the same issue.
3. Create a new issue when unmatched; otherwise append to an open issue atomically.
4. On reaching 10 reports, generate one agency draft, then mark escalated. Persist or otherwise make the draft retrievable; do not discard it after setting status.
5. For a matching already-escalated issue, return an accurate existing-draft message without appending the eleventh demo submission. This preserves the doc's expected ten reporters and ten notices.
6. Resolve an issue explicitly, then generate one notice per unique stored reporter. Return the notices for the demo; repeated resolution must not generate another batch.

The source contracts do not fully specify atomic escalation, draft persistence, retries, or notification history. Agree on internal helpers/storage fields before wiring these together. A draft failure must leave the issue retryable; consider counts at or above the threshold when retrying. Concurrent submissions must not create multiple escalation artifacts. If the hackathon implementation only supports serial execution, document and demonstrate that limitation rather than claiming concurrency guarantees.

The 10-report threshold is for ordinary neighborhood service requests. The prototype is not an emergency reporting service; do not present waiting for ten reports as an emergency response policy.

## Verification and demo acceptance

Use fixtures and mocked external responses for repeatable checks, then run one integration demonstration with configured Mistral and Elasticsearch. Add tests for meaningful lifecycle and parsing behavior as implementation lands; documentation-only edits require review and diff checks, not application tests.

- Ten differently worded mattress reports at one corner produce one issue, count 10, and one agency draft.
- The eleventh matching report receives an existing-escalation message without another draft.
- A different problem 30 meters away remains separate, including a same-category different-object example.
- Resolved issues are excluded from future matching. Resolution generates ten notices for ten unique demo reporters.
- Check outside-radius and older-than-14-days candidates, vague input, invalid coordinates, malformed model output, and draft failure/retry.
- Show a measured duplicate count from SF311, the issues mapping, the geo query, and the resulting issue in Kibana or Dev Tools.
- Keep screenshots as a demo fallback and label recorded or mocked output. Never represent generated notices as delivered messages.

When time slips, the source doc cuts Mistral match confirmation first, then resolution notices, then agency aggregation. Record any cut clearly; removing confirmation means the same-category different-object guarantee no longer holds. Preserve classification, geo matching, and threshold escalation.

Before handing off, report what changed, which checks ran, any external access limitations, and any remaining mock behavior. Keep README commands synchronized with the actual project; do not claim tests passed without running them.

## Integrated application extension (user-authorized)

The full website request supersedes the earlier ownership/MVP limits. website.py is the shared Flask entrypoint; templates/ and static/ are its responsive UI. app.py, data/, notebooks/, ui_server.py, and web/ remain preserved research/tools. store.py owns SQLite accounts, issue documents, reports, events, activities, participants, contribution evidence references, reviews, ledger, settings, and unique issue/reporter notices. es_store.py owns safe_issues search projection; pipeline.py retains submit_report and resolve public signatures and adds submit(..., key, photo) for structured web results and idempotency. Reporter arguments are registered user IDs. The create_issue compatibility function creates one distinct issue with its first report; add_report appends to an open issue; orchestration should use pipeline.submit to enforce threshold drafts. mark_escalated generates a draft and mark_resolved generates notices, rather than bypassing workflow invariants.

The original requirement for atomic Elasticsearch increments is superseded by authoritative SQLite BEGIN IMMEDIATE transactions with an Elasticsearch search projection. This is an intentional storage contract extension: every retrieval synchronizes committed dirty projections before matching; no silent backend failover is allowed. safe_issues avoids overwriting existing team indexes. See DEPLOYMENT.md for operations and the single-host limitation.

Reviewers are administrator accounts granted through the operator CLI. Self-review is rejected. Pending uploads earn no points. Initial configurable reward is 50 points per approved contribution; each review transition records an auditable ledger delta, including reversal. Explicit resolution remains separate from contribution approval. No AI photo verification or external delivery is implemented. Community activities and completion claims are currently restricted to nonresolved illegal_dumping cleanup issues; the UI directs hazardous material and professional work to qualified organizations.

New environment variables: SAFE_SECRET_KEY, SAFE_ENV, SAFE_STORAGE, SAFE_DB, SAFE_SEARCH_BACKEND, ES_URL, ES_API_KEY. Existing Mistral variables remain unchanged. Never commit instance/, uploads, SQLite files, or secret env files. Use requirements-web.txt for this app rather than the preserved research requirements.txt. Run the journey suite before lifecycle changes, including permissions, retries, reversal, and report ten/eleven. Current evidence is recorded in DEPLOYMENT.md; tests use mocked providers and do not prove live model or Elasticsearch service quality.
