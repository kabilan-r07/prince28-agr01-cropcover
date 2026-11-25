"""Ask the CropCover API and print streamed pieces plus timing and cost metadata."""

import argparse
import json
import sys
import time

import httpx


def show_problem(response: httpx.Response) -> int:
    try:
        body = json.loads(response.read())
        detail = body.get("detail") or body
    except ValueError:
        detail = response.text[:300]
    print(f"HTTP {response.status_code}: {detail}")
    return 1


def summary(info: dict, first: float | None, total: float) -> None:
    waited = f"first words after {first:.2f} s, " if first is not None else ""
    print(f"\n--- {info['provider']} / {info['model']}: {waited}total {total:.2f} s")
    print(
        f"    tokens in={info['tokens_in']} out={info['tokens_out']}  "
        f"cost Rs {info['cost_inr']:.6f}  attempts={info['attempts']}  "
        f"fallback={'YES' if info['fallback_used'] else 'no'}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("message")
    parser.add_argument("--url", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--json", action="store_true", help="request one JSON reply")
    args = parser.parse_args()
    sys.stdout.reconfigure(errors="replace")
    url = args.url.rstrip("/") + "/v1/chat"
    started, first = time.perf_counter(), None
    try:
        with httpx.stream(
            "POST", url, json={"message": args.message, "stream": not args.json}, timeout=120
        ) as response:
            if response.status_code != 200:
                return show_problem(response)
            if args.json:
                body = json.loads(response.read())
                print(body.pop("answer"))
                summary(body, None, time.perf_counter() - started)
                return 0
            event = ""
            for line in response.iter_lines():
                if line.startswith("event:"):
                    event = line[6:].strip()
                elif line.startswith("data:"):
                    data = json.loads(line[5:])
                    if event == "done":
                        summary(data, first, time.perf_counter() - started)
                    elif event == "error":
                        print(f"\n--- the answer stopped: {data.get('detail')}")
                        return 1
                    else:
                        first = first or time.perf_counter() - started
                        print(data["delta"], end="", flush=True)
                elif not line:
                    event = ""
    except httpx.TransportError as exc:
        print(f"{type(exc).__name__}: is the API running at {args.url}?")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
