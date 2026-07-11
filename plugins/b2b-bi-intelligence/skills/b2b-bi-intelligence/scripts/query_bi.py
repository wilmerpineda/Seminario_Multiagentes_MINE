from __future__ import annotations

import argparse
import json
import os
import urllib.request


def request(path: str, payload: dict | None = None) -> dict:
    base = os.getenv("BI_API_URL", "http://localhost:8000").rstrip("/")
    key = os.getenv("API_KEY", "session8-local-key")
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(base + path, data=data, headers={"X-API-Key": key, "Content-Type": "application/json"}, method="POST" if data else "GET")
    with urllib.request.urlopen(req, timeout=60) as response:
        return json.load(response)


def main() -> int:
    parser = argparse.ArgumentParser(description="Cliente de la API BI de la sesión 8")
    sub = parser.add_subparsers(dest="command", required=True)
    query = sub.add_parser("query")
    query.add_argument("--question", required=True)
    query.add_argument("--region")
    run = sub.add_parser("run")
    run.add_argument("--run-id", required=True)
    args = parser.parse_args()
    result = request("/v1/query", {"question": args.question, "filters": {"region": args.region}}) if args.command == "query" else request(f"/v1/runs/{args.run_id}")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
