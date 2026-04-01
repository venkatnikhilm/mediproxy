"""
Deepgram Voice Agent helpers for Mediproxy.

Provides configuration builders and connection utilities for the
Deepgram Voice Agent API used by the WebSocket bridge endpoint.
"""

import logging

import websockets

logger = logging.getLogger("shadowguard.voice_agent")

DEEPGRAM_AGENT_URL = "wss://agent.deepgram.com/v1/agent/converse"

# ── Function definitions for Deepgram tool calling ─────────

MITIGATE_FUNCTION_DEF = {
    "name": "mark_mitigated",
    "description": "Mark the PHI event as mitigated after compliance officer confirms.",
    "parameters": {"type": "object", "properties": {}, "required": []},
}

RESOLVE_FUNCTION_DEF = {
    "name": "mark_resolved",
    "description": "Mark the PHI event as resolved after compliance officer confirms.",
    "parameters": {"type": "object", "properties": {}, "required": []},
}


# ── System prompt builder ──────────────────────────────────

def _build_system_prompt(event_data: dict) -> str:
    """Build a concise system prompt injecting PHI event context.

    The prompt instructs the agent to behave as a spoken-word compliance
    assistant — short sentences, no markdown, confirmation before actions.
    """
    ai_service = event_data.get("ai_service", "unknown service")
    phi_types = event_data.get("phi_types", [])
    if isinstance(phi_types, list):
        phi_types = ", ".join(phi_types) if phi_types else "unknown"
    risk_score = event_data.get("risk_score", "N/A")
    severity = event_data.get("severity", "unknown")
    source_ip = event_data.get("source_ip", "unknown")
    redacted_text = event_data.get("redacted_text", "")
    timestamp = event_data.get("timestamp", "unknown")

    # Extract patient name from phi_findings if present
    patient_name = None
    findings = event_data.get("phi_findings", [])
    if isinstance(findings, list):
        for f in findings:
            if isinstance(f, dict) and f.get("type") == "PERSON" and f.get("value"):
                patient_name = f["value"]
                break

    patient_line = f"Patient name: {patient_name}\n" if patient_name else ""

    return (
        "You are the MediProxy compliance assistant. "
        "You are on a phone call with a compliance officer about a PHI exposure event.\n\n"
        f"Service: {ai_service}\n"
        f"PHI types: {phi_types}\n"
        f"{patient_line}"
        f"Risk score: {risk_score}\n"
        f"Severity: {severity}\n"
        f"Source IP: {source_ip}\n"
        f"Redacted text: {redacted_text}\n"
        f"Timestamp: {timestamp}\n\n"
        "Instructions:\n"
        "Lead your opening statement with the service name, PHI types detected, and risk score.\n"
        "Ask the officer if they want more detail before elaborating on the full event context.\n"
        "Keep every response to 1 to 3 sentences.\n"
        "Use a conversational spoken tone. Do not use markdown, bullet points, or any written formatting.\n"
        "If the officer asks to mark the event as mitigated or resolved, "
        "you must ask for explicit confirmation before calling mark_mitigated or mark_resolved."
    )


# ── Settings configuration builder ─────────────────────────

def build_settings(event_data: dict) -> dict:
    """Return the SettingsConfiguration message for Deepgram Voice Agent.

    Audio is mulaw 8 kHz to match AWS Connect telephony format.
    """
    return {
        "type": "Settings",
        "audio": {
            "input": {"encoding": "mulaw", "sample_rate": 8000},
            "output": {"encoding": "mulaw", "sample_rate": 8000, "container": "none"},
        },
        "agent": {
            "listen": {"provider": {"type": "deepgram", "model": "nova-2"}},
            "think": {
                "provider": {"type": "open_ai", "model": "gpt-4o-mini"},
                "prompt": _build_system_prompt(event_data),
                "functions": [MITIGATE_FUNCTION_DEF, RESOLVE_FUNCTION_DEF],
            },
            "speak": {"provider": {"type": "deepgram", "model": "aura-2-asteria-en"}},
        },
    }


# ── Deepgram WebSocket connection helper ───────────────────

async def connect_to_deepgram(api_key: str) -> websockets.WebSocketClientProtocol:
    """Open a WebSocket to the Deepgram Voice Agent API.

    Args:
        api_key: Deepgram API key (from DEEPGRAM_API_KEY env var).

    Returns:
        An open WebSocket connection to Deepgram's agent endpoint.
    """
    headers = {"Authorization": f"Token {api_key}"}
    ws = await websockets.connect(DEEPGRAM_AGENT_URL, additional_headers=headers)
    logger.info("Connected to Deepgram Voice Agent API")
    return ws
