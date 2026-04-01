"""
Twilio Voice Alert integration for ShadowGuard.
Triggers automated outbound phone calls for high-risk PHI exposure events
using Twilio REST API + Media Streams for bidirectional WebSocket audio.

Environment variables:
  TELEPHONY_ENABLED=true
  TWILIO_ACCOUNT_SID=...
  TWILIO_AUTH_TOKEN=...
  TWILIO_PHONE_NUMBER=+1XXXXXXXXXX   (your Twilio number)
  ALERT_PHONE_NUMBER=+1XXXXXXXXXX    (number to call)
  CALL_COOLDOWN_SECONDS=300
  SERVICE_HOST=your-domain.com
"""

import os
import threading
import logging
from datetime import datetime, timezone, timedelta
import json

from dotenv import load_dotenv
load_dotenv()

from database import get_cursor, dict_cursor

logger = logging.getLogger("mediproxy.connect")

# ── Configuration ──────────────────────────────────────────
TELEPHONY_ENABLED       = os.getenv("TELEPHONY_ENABLED", "false").lower() == "true"
TWILIO_ACCOUNT_SID      = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN        = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_PHONE_NUMBER     = os.getenv("TWILIO_PHONE_NUMBER", "")
ALERT_PHONE_NUMBER      = os.getenv("ALERT_PHONE_NUMBER", "")
CALL_COOLDOWN_SECONDS   = int(os.getenv("CALL_COOLDOWN_SECONDS", "300"))
SERVICE_HOST            = os.getenv("SERVICE_HOST", "localhost")


def is_configured() -> bool:
    """Check if Twilio telephony is enabled and all required env vars are set."""
    return bool(
        TELEPHONY_ENABLED
        and TWILIO_ACCOUNT_SID
        and TWILIO_AUTH_TOKEN
        and TWILIO_PHONE_NUMBER
        and ALERT_PHONE_NUMBER
    )


def _check_cooldown(source_ip: str) -> bool:
    """Return True if this source_ip had a call within the cooldown window."""
    cutoff = datetime.now(timezone.utc) - timedelta(seconds=CALL_COOLDOWN_SECONDS)
    with get_cursor(cursor_factory=dict_cursor()) as cur:
        cur.execute(
            "SELECT COUNT(*) as cnt FROM vapi_calls WHERE source_ip = %s AND created_at > %s",
            (source_ip, cutoff),
        )
        return cur.fetchone()["cnt"] > 0


def _extract_phi_list(event_data: dict) -> str:
    """Extract a comma-separated string of PHI types from event data."""
    phi_types = event_data.get("phi_types", [])
    if isinstance(phi_types, str):
        try:
            phi_types = json.loads(phi_types)
        except (json.JSONDecodeError, TypeError):
            phi_types = []
    return ", ".join(phi_types) if phi_types else "protected health information"


def _make_vapi_call(call_db_id: int, event_data: dict, broadcast_fn=None):
    """
    Place an outbound call via Twilio REST API.
    Runs in a background thread. Call record already inserted before this runs.
    """
    from twilio.rest import Client

    event_id = event_data.get("event_id")

    try:
        # Construct TwiML URL (http for local dev, https for production)
        scheme = "http" if SERVICE_HOST in ("localhost", "127.0.0.1") else "https"
        twiml_url = f"{scheme}://{SERVICE_HOST}/api/twiml/{call_db_id}"

        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        call = client.calls.create(
            to=ALERT_PHONE_NUMBER,
            from_=TWILIO_PHONE_NUMBER,
            url=twiml_url,
        )

        logger.info("Twilio call initiated: %s for event %s", call.sid, event_id)

        with get_cursor() as cur:
            cur.execute(
                "UPDATE vapi_calls SET call_id = %s, status = 'queued' WHERE id = %s",
                (call.sid, call_db_id),
            )

        if broadcast_fn:
            broadcast_fn({
                "type": "voice_call",
                "data": {
                    "event_id": str(event_id),
                    "call_id": call.sid,
                    "status": "queued",
                    "phone_number": ALERT_PHONE_NUMBER,
                },
            })

    except Exception as e:
        error_msg = str(e)[:500]
        logger.error("Twilio call failed for event %s: %s", event_id, error_msg)
        with get_cursor() as cur:
            cur.execute(
                "UPDATE vapi_calls SET status = 'failed', error_message = %s WHERE id = %s",
                (error_msg, call_db_id),
            )


def maybe_trigger_call(event_data: dict, broadcast_fn=None):
    """
    Check if the event warrants a call and trigger it in a background thread.
    Called from create_event in main.py.
    """
    if not is_configured():
        return

    severity = event_data.get("severity", "")
    risk_score = event_data.get("risk_score", 0) or 0

    if severity not in ("critical", "high") or risk_score < 70:
        return

    # Skip background/telemetry requests
    request_path = event_data.get("request_path", "")
    if any(x in request_path for x in ("prepare", "telemetry", "sentinel")):
        return

    source_ip = event_data.get("source_ip", "")
    if _check_cooldown(source_ip):
        return

    # Insert call record synchronously to block duplicate calls
    event_id = event_data.get("event_id")
    with get_cursor(cursor_factory=dict_cursor()) as cur:
        cur.execute(
            "INSERT INTO vapi_calls (event_id, source_ip, phone_number, status) "
            "VALUES (%s, %s, %s, 'initiated') RETURNING id",
            (event_id, source_ip, ALERT_PHONE_NUMBER),
        )
        call_db_id = cur.fetchone()["id"]

    thread = threading.Thread(
        target=_make_vapi_call,
        args=(call_db_id, event_data, broadcast_fn),
        daemon=True,
    )
    thread.start()
