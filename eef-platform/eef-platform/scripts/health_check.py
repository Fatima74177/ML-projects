"""
health_check.py -- CLI health check across all EEF platform dependencies.
Hits the real /health/* endpoints (no separate logic duplicated here).

Usage:
    python3 scripts/health_check.py [--base-url http://localhost:8000]
"""
import argparse
import json
import sys
import urllib.request
import urllib.error

ENDPOINTS = ["/health", "/health/database", "/health/redis", "/health/kafka",
             "/health/neo4j", "/health/models"]


def check(base_url: str) -> bool:
    all_ok = True
    for path in ENDPOINTS:
        url = f"{base_url}{path}"
        try:
            with urllib.request.urlopen(url, timeout=5) as resp:
                body = json.loads(resp.read())
                status = body.get("status", "unknown")
                marker = "OK" if status in ("ok", "disabled") else "FAIL"
                if status not in ("ok", "disabled"):
                    all_ok = False
                print(f"[{marker}] {path:20s} -> {status}")
        except urllib.error.URLError as e:
            print(f"[FAIL] {path:20s} -> unreachable ({e})")
            all_ok = False
    return all_ok


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://localhost:8000")
    args = parser.parse_args()

    print(f"Checking EEF platform health at {args.base_url} ...\n")
    ok = check(args.base_url)
    print("\nAll systems OK." if ok else "\nOne or more checks FAILED.")
    sys.exit(0 if ok else 1)
