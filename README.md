# SaFe

**Report it once, and it counts.**

SaFe groups matching San Francisco neighborhood reports so residents are heard and agencies receive a clearer signal. Built for the Mistral + Elastic hackathon.

Read [AGENTS.md](AGENTS.md) for shared contracts and [BRANDING.md](BRANDING.md) for product copy and visual guidance.

The broader [product vision](PRODUCT_VISION.md) connects reporting with NGO/community action, completion review, and contributor rewards. It records the user's gamification direction, proposed volunteer activities, and what remains to be built. The shared [SaFe repository](https://github.com/Ani454/SaFe) also has a Streamlit SF311 exploration app on `main`; this branch documents and runs the Person B workspace below. Source inspection does not verify that either app is deployed or that the full product is online.

For the pitch and integration demo, read [JUDGING.md](JUDGING.md): the published criteria (Novelty, Use of Elastic, Use of Mistral), a two-minute initial demo and three-minute finalist plan, and the evidence still needed. The central demonstration is ten differently worded reports becoming one issue and one reviewable agency draft, while a different object nearby stays separate. This combined lifecycle goes beyond classification and nearby-case retrieval in the organizer's starter idea. It is the integration target; the current checkout provides the Person B workspace described below.

## Person B: Mistral workspace

All four agreed functions are in [mistral_ai.py](mistral_ai.py), with a responsive local UI for report classification, comparing descriptions, drafting agency emails, and drafting resolution notices.

Elasticsearch storage, geo filtering, aggregation, threshold enforcement, and the shared lifecycle pipeline belong to Persons A and C. They are not implemented by this UI. Editing example issue details does not update a database.

## Run locally

Requires Python 3.10 or newer. No third-party packages or frontend build needed.

~~~sh
python3 ui_server.py
~~~

Open [http://127.0.0.1:8000](http://127.0.0.1:8000). **Try a sample** on any tool loads an illustrative fixture without credentials. The preview replaces the form with matching sample inputs and is labeled **Sample preview**. It is not model output. Editing an input clears the old result.

For live Mistral requests:

~~~sh
cp .env.example .env
~~~

Set your key in the local, ignored .env file:

~~~dotenv
MISTRAL_API_KEY=your-key-here
MISTRAL_MODEL=mistral-small-latest
MISTRAL_TIMEOUT_SECONDS=30
~~~

Restart the server, then use the primary action. Environment variables take precedence over .env. The UI shows whether a key is configured, which does not verify its validity. Errors from live requests are displayed without falling back to fixtures.

The server binds to 127.0.0.1 only. For another port: python3 ui_server.py --port 8001. This is a local development server, not a production hosting setup.

## Import from the shared pipeline

~~~python
from mistral_ai import (
    classify_report,
    is_same_issue,
    draft_authority_email,
    draft_resolution_notice,
    ClarificationNeeded,
    MistralError,
)
~~~

Public signatures match AGENTS.md. Set MISTRAL_API_KEY in the process environment when importing directly; only ui_server.py loads .env.

Classification returns exactly category, summary, and severity (integer 1–5). Categories: illegal_dumping, graffiti, streetlight, pothole, other. Ambiguous reports raise ClarificationNeeded; configuration, provider, and model output failures raise MistralError. Invalid caller arguments raise ValueError. Leave reports unmerged and drafts retryable on errors.

Both draft functions require category, summary, numeric location.lat and location.lon, positive report_count, created_at, and updated_at. Timestamps must be chronological ISO 8601 values with timezones. Resolution drafts additionally require status resolved; optional resolution text supplies the recorded outcome. Functions do not change status, count reports, send messages, or write storage. Reporter identities and raw report history are excluded from draft requests.

Uses the [official Mistral chat completions REST API](https://docs.mistral.ai/api/endpoint/chat) through standard-library HTTP, with JSON object mode, explicit output instructions, low temperature, bounded tokens, a timeout, and local validation. No SDK dependency is required.

## Verification

~~~sh
python3 -m unittest discover -s tests -v
node --check web/app.js
git diff --check
~~~

Tests mock Mistral and cover parsing, strict booleans and priorities, vague reports, provider failures, issue validation, privacy exclusions, and local HTTP routes. They do not prove live model quality. A live model run requires a valid key and network access; Elasticsearch integration requires the other workstreams.

All email and notice outputs are drafts. Nothing is sent. Sample counts and coordinates are synthetic fixtures. No SF311 statistic is shown until measured against the actual dataset.
