"""
Unit tests for the Voice Agent bridge endpoint, TwiML endpoint, and helpers.

Covers:
- Bridge endpoint registration
- Missing API key handling (1008 close)
- System prompt identity check
- PATCH failure error handling
- Audio config in build_settings
- TwiML endpoint (response code, content type, XML body)
- _make_vapi_call signature

Requirements: 1.1, 1.5, 2.1, 2.2, 2.3, 6.1, 7.2
"""

import inspect
import json
import os
from unittest.mock import patch, MagicMock, AsyncMock

import pytest
from fastapi.testclient import TestClient

SAMPLE_EVENT = {
    "event_id": "abc-123",
    "ai_service": "ChatGPT",
    "phi_types": ["SSN", "DOB"],
    "risk_score": 92,
    "severity": "critical",
    "source_ip": "10.0.0.1",
    "redacted_text": "Patient [REDACTED] was seen on [REDACTED]",
    "timestamp": "2025-06-01T12:00:00Z",
}


def test_bridge_endpoint_registered():
    """Verify /api/voice-agent/{call_db_id} route exists."""
    from main import app

    ws_routes = [
        r.path for r in app.routes
        if hasattr(r, "path") and "voice-agent" in r.path
    ]
    assert "/api/voice-agent/{call_db_id}" in ws_routes


@pytest.mark.asyncio
async def test_missing_api_key_closes_1008():
    """With DEEPGRAM_API_KEY unset, the bridge must finalize as failed."""
    from main import _finalize_call, voice_agent_bridge

    mock_ws = AsyncMock()
    mock_ws.accept = AsyncMock()
    mock_ws.close = AsyncMock()
    mock_ws.client_state = "CONNECTED"

    env = {k: v for k, v in os.environ.items() if k != "DEEPGRAM_API_KEY"}

    with patch.dict(os.environ, env, clear=True), \
         patch("main._finalize_call", new_callable=AsyncMock) as mock_fin:
        await voice_agent_bridge(mock_ws, 1)

        # Should have closed with 1008
        mock_ws.close.assert_called_once()
        close_kwargs = mock_ws.close.call_args
        assert close_kwargs[1].get("code", close_kwargs[0][0] if close_kwargs[0] else None) == 1008

        # Should have finalized as failed
        mock_fin.assert_called_once()
        assert mock_fin.call_args[0][1] == "failed"


def test_system_prompt_contains_identity():
    """Known event must produce prompt with 'ShadowGuard compliance assistant'."""
    from deepgram_agent import _build_system_prompt

    prompt = _build_system_prompt(SAMPLE_EVENT)
    assert "ShadowGuard compliance assistant" in prompt


def test_system_prompt_contains_event_fields():
    """The prompt must include all key event fields."""
    from deepgram_agent import _build_system_prompt

    prompt = _build_system_prompt(SAMPLE_EVENT)
    assert "ChatGPT" in prompt
    assert "SSN" in prompt
    assert "DOB" in prompt
    assert "92" in prompt
    assert "critical" in prompt
    assert "10.0.0.1" in prompt
    assert "[REDACTED]" in prompt
    assert "2025-06-01T12:00:00Z" in prompt


@pytest.mark.asyncio
async def test_patch_failure_returns_error_response():
    """When the DB update raises, _patch_event_status returns error string."""
    from main import _patch_event_status

    with patch("main.get_cursor") as mock_gc:
        ctx = MagicMock()
        ctx.__enter__ = MagicMock(side_effect=Exception("DB down"))
        ctx.__exit__ = MagicMock(return_value=False)
        mock_gc.return_value = ctx

        result = await _patch_event_status("evt-999", "mitigated", None)

    assert "Could not update status" in result
    assert "manually" in result.lower()


@pytest.mark.asyncio
async def test_patch_event_not_found_returns_error():
    """When event doesn't exist, _patch_event_status returns error string."""
    from main import _patch_event_status

    mock_cur = MagicMock()
    mock_cur.fetchone.return_value = None
    ctx = MagicMock()
    ctx.__enter__ = MagicMock(return_value=mock_cur)
    ctx.__exit__ = MagicMock(return_value=False)

    with patch("main.get_cursor", return_value=ctx):
        result = await _patch_event_status("evt-none", "resolved", None)

    assert "not found" in result.lower()
    assert "manually" in result.lower()


def test_build_settings_audio_config():
    """build_settings must produce mulaw 8kHz audio encoding."""
    from deepgram_agent import build_settings

    settings = build_settings(SAMPLE_EVENT)

    assert settings["type"] == "Settings"
    audio = settings["audio"]
    assert audio["input"]["encoding"] == "mulaw"
    assert audio["input"]["sample_rate"] == 8000
    assert audio["output"]["encoding"] == "mulaw"
    assert audio["output"]["sample_rate"] == 8000


def test_build_settings_models():
    """build_settings must configure nova-2, gpt-4o-mini, aura-asteria-en."""
    from deepgram_agent import build_settings

    settings = build_settings(SAMPLE_EVENT)
    agent = settings["agent"]

    assert agent["listen"]["provider"]["model"] == "nova-2"
    assert agent["think"]["provider"]["model"] == "gpt-4o-mini"
    assert agent["speak"]["provider"]["model"] == "aura-2-asteria-en"


def test_build_settings_includes_functions():
    """build_settings must include mitigate and resolve function defs."""
    from deepgram_agent import build_settings

    settings = build_settings(SAMPLE_EVENT)
    fn_names = [f["name"] for f in settings["agent"]["think"]["functions"]]

    assert "mark_mitigated" in fn_names
    assert "mark_resolved" in fn_names


# ============================================================
# TwiML Endpoint Tests (Task 7.1)
# Requirements: 2.1, 2.2, 2.3
# ============================================================

def test_twiml_endpoint_registered():
    """GET /api/twiml/1 returns 200."""
    from main import app

    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/api/twiml/1")
    assert response.status_code == 200


def test_twiml_content_type():
    """Response has Content-Type: application/xml."""
    from main import app

    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/api/twiml/1")
    assert "application/xml" in response.headers["content-type"]


def test_twiml_contains_say_and_stream():
    """XML contains <Say> greeting and <Stream> element."""
    from main import app

    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/api/twiml/1")
    body = response.text

    assert "<Say>" in body
    assert "ShadowGuard compliance agent" in body
    assert "<Stream" in body
    assert "voice-agent/1" in body


# ============================================================
# Bridge and Caller Tests for Twilio (Task 7.2)
# Requirements: 1.1, 6.1
# ============================================================

def test_make_vapi_call_signature_unchanged():
    """_make_vapi_call accepts (call_db_id, event_data, broadcast_fn)."""
    from vapi_caller import _make_vapi_call

    sig = inspect.signature(_make_vapi_call)
    params = list(sig.parameters.keys())
    assert params == ["call_db_id", "event_data", "broadcast_fn"]
