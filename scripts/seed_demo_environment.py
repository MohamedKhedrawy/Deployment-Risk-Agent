#!/usr/bin/env python3
"""Seed Demo Environment — injects realistic historical events into Dynatrace.

Run this once before recording a demo to populate realistic incident history
on payment-service and auth-service so the RISKY and FATAL mock scenarios
have plausible context in the actual Dynatrace timeline.

Usage:
    python scripts/seed_demo_environment.py
    # or
    make seed-demo
"""

from __future__ import annotations

import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv

load_dotenv()

DT_ENV = os.getenv("DT_ENVIRONMENT", "").rstrip("/")
CLIENT_ID = os.getenv("OAUTH_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("OAUTH_CLIENT_SECRET", "")


def _get_token() -> str:
    """Obtain an OAuth access token from Dynatrace SSO."""
    env_id = DT_ENV.split("//")[1].split(".")[0] if "//" in DT_ENV else ""
    data = urllib.parse.urlencode({
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "resource": f"urn:dtenvironment:{env_id}",
    }).encode("ascii")

    req = urllib.request.Request(
        "https://sso.dynatrace.com/sso/oauth2/token",
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())["access_token"]


def _send_event(token: str, entity_id: str, title: str, ts_ms: int, properties: dict) -> bool:
    """Push a CUSTOM_INFO event to Dynatrace Events API v2."""
    payload = json.dumps({
        "eventType": "CUSTOM_INFO",
        "title": title,
        "startTime": ts_ms,
        "endTime": ts_ms + 3_600_000,  # 1 hour duration
        "entitySelector": f"entityId({entity_id})",
        "properties": properties,
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{DT_ENV}/api/v2/events/ingest",
        data=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.status == 201
    except urllib.error.HTTPError as e:
        print(f"  ⚠️  HTTP {e.code}: {e.read().decode()[:200]}")
        return False


def _find_entity(token: str, name_fragment: str, entity_type: str = "SERVICE") -> str | None:
    """Search for a Dynatrace entity by name fragment, returns entityId or None."""
    selector = urllib.parse.quote(f'type("{entity_type}"),entityName.contains("{name_fragment}")')
    url = f"{DT_ENV}/api/v2/entities?entitySelector={selector}&pageSize=1"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
            entities = data.get("entities", [])
            if entities:
                return entities[0]["entityId"]
    except Exception as e:
        print(f"  ⚠️  Entity search failed for '{name_fragment}': {e}")
    return None


def main():
    if not DT_ENV or not CLIENT_ID or not CLIENT_SECRET:
        print("❌ Missing environment variables. Set DT_ENVIRONMENT, OAUTH_CLIENT_ID, and OAUTH_CLIENT_SECRET in .env")
        sys.exit(1)

    print(f"🌱 Seeding Dynatrace demo environment: {DT_ENV}")
    print()

    # Authenticate
    print("🔑 Authenticating...")
    try:
        token = _get_token()
        print("   ✅ Token obtained")
    except Exception as e:
        print(f"   ❌ Auth failed: {e}")
        sys.exit(1)

    now = datetime.now(timezone.utc)
    created = []

    # ── payment-service: 3 historical incidents ────────────────────────
    print("\n📦 Finding payment-service...")
    payment_id = _find_entity(token, "payment")
    if not payment_id:
        # Fallback: use a placeholder and note it
        payment_id = "PLACEHOLDER_PAYMENT"
        print("   ⚠️  payment-service not found in topology. Using placeholder.")
    else:
        print(f"   ✅ Found: {payment_id}")

    payment_events = [
        {
            "title": "🐤 [Demo Seed] Payment service elevated error rate",
            "offset_days": 5,
            "props": {
                "canary.event.type": "INCIDENT_HISTORY",
                "canary.error_rate": "3.2%",
                "canary.duration_minutes": "47",
                "canary.seeded_by": "seed_demo_environment.py",
            },
        },
        {
            "title": "🐤 [Demo Seed] Payment gateway timeout spike",
            "offset_days": 14,
            "props": {
                "canary.event.type": "INCIDENT_HISTORY",
                "canary.error_rate": "1.8%",
                "canary.duration_minutes": "23",
                "canary.seeded_by": "seed_demo_environment.py",
            },
        },
        {
            "title": "🐤 [Demo Seed] Payment SLO budget warning",
            "offset_days": 22,
            "props": {
                "canary.event.type": "SLO_WARNING",
                "canary.slo_current": "95.1%",
                "canary.slo_target": "99.9%",
                "canary.seeded_by": "seed_demo_environment.py",
            },
        },
    ]

    print("\n📅 Creating payment-service historical events...")
    for ev in payment_events:
        ts = int((now - timedelta(days=ev["offset_days"])).timestamp() * 1000)
        ok = _send_event(token, payment_id, ev["title"], ts, ev["props"])
        status = "✅" if ok else "⚠️ "
        print(f"   {status} {ev['title'][:60]} (T-{ev['offset_days']}d)")
        if ok:
            created.append(ev["title"])

    # ── auth-service: active problem simulation ────────────────────────
    print("\n📦 Finding auth-service...")
    auth_id = _find_entity(token, "auth")
    if not auth_id:
        auth_id = "PLACEHOLDER_AUTH"
        print("   ⚠️  auth-service not found in topology. Using placeholder.")
    else:
        print(f"   ✅ Found: {auth_id}")

    print("\n🔴 Creating auth-service active problem simulation...")
    ts_now = int(now.timestamp() * 1000)
    auth_events = [
        {
            "title": "🐤 [Demo Seed] ACTIVE: Auth service OAuth provider failure",
            "offset_days": 0,
            "props": {
                "canary.event.type": "ACTIVE_PROBLEM",
                "canary.error_rate": "8.7%",
                "canary.slo_current": "87.0%",
                "canary.impact": "89% of users",
                "canary.status": "OPEN",
                "canary.seeded_by": "seed_demo_environment.py",
            },
        },
        {
            "title": "🐤 [Demo Seed] Auth service repeated authentication failures",
            "offset_days": 3,
            "props": {
                "canary.event.type": "INCIDENT_HISTORY",
                "canary.error_rate": "4.2%",
                "canary.seeded_by": "seed_demo_environment.py",
            },
        },
    ]

    for ev in auth_events:
        ts = int((now - timedelta(days=ev["offset_days"])).timestamp() * 1000)
        ok = _send_event(token, auth_id, ev["title"], ts, ev["props"])
        status = "✅" if ok else "⚠️ "
        print(f"   {status} {ev['title'][:60]}")
        if ok:
            created.append(ev["title"])

    # ── Summary ────────────────────────────────────────────────────────
    print(f"\n✅ Seeding complete. {len(created)} events created.")
    print("\nThese events will appear on the service timelines in Dynatrace.")
    print("The Canary Whisperer's RISKY and FATAL demo scenarios now have")
    print("realistic incident context visible in your environment.")
    print()
    print("Run `make run-all` to start the application.")


if __name__ == "__main__":
    main()
