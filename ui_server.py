"""Local-only Person B workspace. Run: python3 ui_server.py."""
from __future__ import annotations

import argparse
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import mistral_ai as ai

ROOT = Path(__file__).resolve().parent


def load_env():
    path = ROOT / ".env"
    if path.exists():
        for line in path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            if key.strip() in {"MISTRAL_API_KEY", "MISTRAL_MODEL", "MISTRAL_TIMEOUT_SECONDS", "SAFE_SECRET_KEY", "SAFE_ENV", "SAFE_STORAGE", "SAFE_DB", "SAFE_SEARCH_BACKEND", "ES_URL", "ES_API_KEY"}:
                os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


def run_action(action, data):
    if action == "classify":
        return ai.classify_report(data.get("text"))
    if action == "match":
        return {"same_issue": ai.is_same_issue(data.get("text"), data.get("existing_summary"))}
    if action == "agency":
        return {"draft": ai.draft_authority_email(data.get("issue"), data.get("agency"))}
    if action == "resolution":
        return {"draft": ai.draft_resolution_notice(data.get("issue"))}
    raise ValueError("Unknown action.")


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Do not log request payloads or reporter text.
        pass

    def reply(self, status, body, mime="application/json"):
        raw = json.dumps(body).encode() if mime == "application/json" else body
        self.send_response(status)
        self.send_header("Content-Type", mime + "; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'")
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        if self.path == "/api/config":
            return self.reply(200, {"configured": bool(os.environ.get("MISTRAL_API_KEY", "").strip()),
                                    "model": os.environ.get("MISTRAL_MODEL", "mistral-small-latest")})
        paths = {"/": ("index.html", "text/html"), "/app.js": ("app.js", "text/javascript"),
                 "/styles.css": ("styles.css", "text/css")}
        if self.path not in paths:
            return self.reply(404, {"error": "Not found."})
        name, mime = paths[self.path]
        self.reply(200, (ROOT / "web" / name).read_bytes(), mime)

    def do_POST(self):
        # JSON and same-origin checks prevent other websites driving a local user's key.
        expected_host = f"127.0.0.1:{self.server.server_port}"
        hosts = {expected_host, f"localhost:{self.server.server_port}"}
        origin = self.headers.get("Origin")
        if self.headers.get("Host") not in hosts or (origin and origin not in {f"http://{h}" for h in hosts}):
            return self.reply(403, {"error": "Only local same-origin requests are supported."})
        if self.headers.get("Content-Type", "").split(";")[0] != "application/json":
            return self.reply(415, {"error": "Use application/json."})
        if self.path not in {"/api/classify", "/api/match", "/api/agency", "/api/resolution"}:
            return self.reply(404, {"error": "Not found."})
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if not 0 < size <= 24000:
                return self.reply(413, {"error": "Request must be between 1 and 24000 bytes."})
            data = json.loads(self.rfile.read(size))
            if not isinstance(data, dict):
                raise ValueError("Request must be a JSON object.")
            result = run_action(self.path.removeprefix("/api/"), data)
            self.reply(200, {"result": result, "mode": "live"})
        except ai.ClarificationNeeded as exc:
            self.reply(422, {"error": str(exc), "needs_clarification": True})
        except ai.MistralError as exc:
            self.reply(503, {"error": str(exc)})
        except (ValueError, TypeError, UnicodeError) as exc:
            self.reply(400, {"error": str(exc)})
        except Exception:
            self.reply(500, {"error": "The request could not be completed. Please try again."})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    load_env()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"SaFe workspace: http://127.0.0.1:{args.port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
