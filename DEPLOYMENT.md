# Deploy the integrated website

The deployable entrypoint is website:create_app(), served by Gunicorn. app.py and ui_server.py are preserved research/development tools; do not run three services for the product.

## Local setup

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements-web.txt
cp .env.example .env
# Edit .env with ES_URL, ES_API_KEY, MISTRAL_API_KEY.
.venv/bin/flask --app website:create_app run --port 8001
```

Open http://127.0.0.1:8001. For local exploration without Elasticsearch explicitly select SAFE_SEARCH_BACKEND=sqlite. The visible banner identifies this fallback. There is no automatic fallback when Elasticsearch or Mistral fails, and no hardcoded model output in the integrated app.

Register a resident account. To designate a reviewer, an operator runs:

```sh
.venv/bin/flask --app website:create_app make-admin
```

Supply an existing registered email at the prompt. No default administrator or shared password is shipped. Admins cannot approve their own contributions. Registration does not verify email ownership; this is a hackathon authentication system without password recovery or identity verification.

## Container deployment

1. Provision a Docker-capable host with HTTPS termination and a durable local volume mounted at /data. Use one application replica. SQLite is intentionally a single-host transactional store; do not put its database on a network filesystem or horizontally scale independent copies.
2. Supply SAFE_ENV=production, a random stable SAFE_SECRET_KEY (at least 32 random bytes), SAFE_STORAGE=/data, SAFE_DB=/data/safe.db, SAFE_SEARCH_BACKEND=elasticsearch, ES_URL, ES_API_KEY, MISTRAL_API_KEY, MISTRAL_MODEL and MISTRAL_TIMEOUT_SECONDS. ES_URL must be reachable from the container; localhost would refer to the container itself. Secrets belong in the deployment environment, not the image.
3. Build and start:

```sh
docker build -t safe-web .
docker run --rm -p 127.0.0.1:8000:8000 --env-file .env.production -v safe-data:/data safe-web
```

A named Docker volume is initialized writable for the nonroot app user. A host bind mount must be made writable for that user. Keep .env.production outside the build context (or add it to .dockerignore); never commit it. Only expose the loopback port through a TLS reverse proxy. Production cookies require HTTPS. The app does not need forwarded headers to authenticate and does not blindly trust them.

4. Check /healthz, register an account via HTTPS, and grant the reviewer role using the Flask CLI in the running container. The health endpoint checks SQLite, not external provider validity.
5. Run flask --app website:create_app sync-search in the container to create the safe_issues projection and index pending issues. The first report also synchronizes pending projections before retrieval. The SF311 page reads the existing sf311 index without modifying it.
6. Exercise a live classification and report submission, confirm the actual Elasticsearch candidate query, then the ten/eleven-report and review/reversal sequence. Do not mark live readiness until this is done with valid keys. Roll back the application image without deleting /data if the check fails.

## Persistence, retries, and recovery

SQLite stores accounts, complete issue documents, reports, draft artifacts, activities, participation, contribution evidence references, review history, award ledger, and unique per-reporter notices. Photos are sanitized and reencoded to JPEG under /data/uploads; metadata and original filenames are discarded. The database and uploads must be backed up together. Use SQLite's online backup API or stop the app before copying files; do not copy only the live .db file without its WAL state. Restore onto a new volume, start the same image, and reindex via sync-search. Do not publish backups.

Issue matching defaults to Elasticsearch, constrained by category, 50m, 14 days, and nonresolved status. SQLite remains the canonical transactional record. A dirty flag is a durable search outbox: commits mark changed issues dirty, and the next retrieval or sync-search refreshes them before matching. Elasticsearch receives only the issue projection, not account emails, reporter IDs, or full report texts. The index is safe_issues to avoid touching an existing issues or sf311 index. Index mappings and query code are in es_store.py.

BEGIN IMMEDIATE serializes report selection, increment, draft generation, and resolution against the local database, including across Gunicorn threads. This favors correctness over throughput. Provider calls hold a write lock; a deployment for heavier traffic should move workflows to durable jobs and use a server database. The configured process timeout exceeds provider timeouts. A request key prevents duplicate attached reports on resubmission. Repeated escalation, repeated review decisions, revocations, and repeated resolution do not create duplicate artifacts. A failure before matching creates no report; a draft failure after attachment persists the report with a retry flag. Notice generation failure rolls back resolution so an admin can retry.

Initial point rule: 50 points per approved contribution, zero for reports or unreviewed evidence. This is a product choice, adjustable by an administrator. Rule changes affect future approvals, not existing ledger entries. A revocation writes an offsetting entry for that contribution's actual existing balance. Reapproval creates a new review and restores the current configured award; it does not erase history. Separate claims still require independent human review; this is not an identity-verified anti-fraud program.

Leaflet 1.9.4 is pinned at the CDN URL; OpenStreetMap supplies map tiles. The accessible list and coordinate entry work without the map. Deployment requires outbound HTTPS to Mistral, Elasticsearch, and these map assets. No automatic photo verification, agency delivery, emergency handling, or city submission is performed.

## Verification performed and remaining environment checks

The automated suite uses real temporary SQLite databases, Flask HTTP requests, uploaded image files, mocked Mistral outputs, and a checked Elasticsearch query shape. Tests do not substitute for live model/Elasticsearch verification. The current workstation has no .env/provider credentials and no Docker executable. The Dockerfile is prepared but image build and cloud deployment have not been run here.

```sh
.venv/bin/python -m unittest discover -s tests -v
node --check static/site.js
node --check web/app.js
```

Before public use, arrange a reviewer policy, moderation of resident text/photos, and privacy/retention expectations appropriate to the deployment. Do not claim verified identities, fraud prevention, city affiliation, or measured city impact.
