"""Minimal smoke checks against a running API (production or local).

Usage (PowerShell):
  $env:SMOKE_BASE_URL = "https://api.ciatec.org"
  python scripts/smoke_production.py

Requires: GET /health returns 200 (DB reachable), POST /api/v1/auth/login returns 401.
"""

from __future__ import annotations

import asyncio
import os
import sys

import httpx


async def main() -> int:
    base = os.environ.get("SMOKE_BASE_URL", "").rstrip("/")
    if not base:
        print(
            "Set SMOKE_BASE_URL to the API root (e.g. https://api.ciatec.org)",
            file=sys.stderr,
        )
        return 2

    async with httpx.AsyncClient(base_url=base, timeout=30.0) as client:
        h = await client.get("/health")
        if h.status_code != 200:
            print(f"GET /health expected 200, got {h.status_code}", file=sys.stderr)
            return 1

        bad = await client.post(
            "/api/v1/auth/login",
            json={"email": "smoke@example.com", "password": "wrong"},
        )
        if bad.status_code != 401:
            print(
                f"POST /auth/login with bad creds expected 401, got {bad.status_code}",
                file=sys.stderr,
            )
            return 1

    print("Smoke OK:", base)
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
