"""Check that the live API is healthy and serving documents."""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections.abc import Mapping
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def get_json(url: str) -> tuple[int, object]:
    request = Request(url, headers={"Accept": "application/json"})
    try:
        with urlopen(request, timeout=10) as response:
            return response.status, json.load(response)
    except HTTPError as error:
        return error.code, error.read().decode("utf-8", errors="replace")


def check_once(base_url: str, expected_version: str | None) -> tuple[bool, str]:
    try:
        status, health = get_json(f"{base_url}/health")
        version = health.get("version") if isinstance(health, Mapping) else None
        if status != 200 or not isinstance(health, Mapping) or health.get("status") != "ok":
            return False, f"/health -> {status} {health}"
        if expected_version and version != expected_version:
            return False, (
                f"/health -> {status}, waiting for version {expected_version}; "
                f"live version {version}"
            )

        status, ready = get_json(f"{base_url}/ready")
        checks = ready.get("checks") if isinstance(ready, Mapping) else None
        if (
            status != 200
            or not isinstance(ready, Mapping)
            or ready.get("status") != "ready"
            or not isinstance(checks, Mapping)
            or checks.get("database") is not True
        ):
            return False, f"/ready -> {status} {ready}"

        status, documents = get_json(f"{base_url}/v1/documents?limit=1")
        if (
            status != 200
            or not isinstance(documents, Mapping)
            or not isinstance(documents.get("items"), list)
            or not documents["items"]
        ):
            return False, f"/v1/documents?limit=1 -> {status} {documents}"

        return True, f"version {version}; database ready; documents serving"
    except (TimeoutError, URLError, ValueError) as error:
        return False, str(error)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url", help="Base URL of the deployed service")
    parser.add_argument("--expect-version", help="Wait for this commit SHA to become live")
    parser.add_argument(
        "--timeout", type=int, default=600, help="Maximum wait in seconds (default: 600)"
    )
    args = parser.parse_args()

    base_url = args.url.rstrip("/")
    deadline = time.monotonic() + args.timeout
    while True:
        ok, message = check_once(base_url, args.expect_version)
        prefix = "ok" if ok else "waiting"
        print(f"{prefix} {message}", flush=True)
        if ok:
            print("Smoke test passed")
            return 0
        if time.monotonic() >= deadline:
            print(f"Smoke test failed after {args.timeout}s", file=sys.stderr)
            return 1
        time.sleep(min(10, max(1, deadline - time.monotonic())))


if __name__ == "__main__":
    raise SystemExit(main())
