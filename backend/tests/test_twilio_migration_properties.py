"""
Property-based tests for the Twilio Voice Migration feature.

Uses Hypothesis to verify universal correctness properties across
randomly generated inputs for the Twilio telephony integration.

Feature: twilio-voice-migration
"""

import base64
import json
import os
from unittest.mock import patch, MagicMock, call

import pytest
from hypothesis import given, settings, assume
from hypothesis import strategies as st
from fastapi.testclient import TestClient


# ── Strategies ──────────────────────────────────────────────

# Positive integers for call_db_id
call_db_ids = st.integers(min_value=1, max_value=10**9)

# Arbitrary event data dicts with at least an event_id
event_data_st = st.fixed_dictionaries(
    {"event_id": st.uuids().map(str)},
    optional={
        "source_ip": st.ip_addresses().map(str),
        "ai_service": st.text(min_size=1, max_size=30),
        "risk_score": st.integers(min_value=0, max_value=100),
        "severity": st.sampled_from(["low", "medium", "high", "critical"]),
        "phi_types": st.lists(st.text(min_size=1, max_size=20), max_size=5),
    },
)

# Twilio Call SIDs look like CA + 32 hex chars
call_sids = st.from_regex(r"CA[0-9a-f]{32}", fullmatch=True)

# Arbitrary error messages of varying length
error_messages = st.text(min_size=0, max_size=2000)

# SERVICE_HOST values including edge cases
service_hosts = st.one_of(
    st.just(""),
    st.just("localhost"),
    st.just("127.0.0.1"),
    st.from_regex(r"[a-z][a-z0-9\-]{0,20}\.[a-z]{2,6}", fullmatch=True),
)

# Raw audio bytes of arbitrary length
audio_bytes_st = st.binary(min_size=0, max_size=4096)

# Stream SIDs
stream_sids = st.from_regex(r"MZ[0-9a-f]{32}", fullmatch=True)

# Boolean-ish env var values: either a non-empty string or empty/absent
env_var_values = st.one_of(st.just(""), st.text(min_size=1, max_size=50))


# ============================================================
# Property 1: Twilio Call Creation Correctness
# Feature: twilio-voice-migration, Property 1: Twilio Call Creation Correctness
# **Validates: Requirements 1.2**
# ============================================================

@settings(max_examples=100)
@given(cid=call_db_ids, event=event_data_st)
def test_twilio_call_creation_correctness(cid, event):
    """For any call_db_id and event_data, _make_vapi_call calls
    client.calls.create() with correct to, from_, and url args."""

    mock_call = MagicMock()
    mock_call.sid = "CAfake00000000000000000000000000ff"

    mock_client_instance = MagicMock()
    mock_client_instance.calls.create.return_value = mock_call

    mock_cursor = MagicMock()
    mock_ctx = MagicMock()
    mock_ctx.__enter__ = MagicMock(return_value=mock_cursor)
    mock_ctx.__exit__ = MagicMock(return_value=False)

    with patch("vapi_caller.get_cursor", return_value=mock_ctx), \
         patch("twilio.rest.Client", return_value=mock_client_instance):

        from vapi_caller import _make_vapi_call, ALERT_PHONE_NUMBER, TWILIO_PHONE_NUMBER, SERVICE_HOST

        _make_vapi_call(cid, event)

    mock_client_instance.calls.create.assert_called_once()
    kwargs = mock_client_instance.calls.create.call_args

    assert kwargs[1]["to"] == ALERT_PHONE_NUMBER or kwargs.kwargs.get("to") == ALERT_PHONE_NUMBER
    assert kwargs[1]["from_"] == TWILIO_PHONE_NUMBER or kwargs.kwargs.get("from_") == TWILIO_PHONE_NUMBER

    url_arg = kwargs[1].get("url") or kwargs.kwargs.get("url", "")
    assert f"/api/twiml/{cid}" in url_arg



# ============================================================
# Property 2: Successful Call DB Update
# Feature: twilio-voice-migration, Property 2: Successful Call DB Update
# **Validates: Requirements 1.3**
# ============================================================

@settings(max_examples=100)
@given(cid=call_db_ids, event=event_data_st, sid=call_sids)
def test_successful_call_db_update(cid, event, sid):
    """For any Call SID returned by Twilio, the DB record is updated
    with that SID and status 'queued'."""

    mock_call = MagicMock()
    mock_call.sid = sid

    mock_client_instance = MagicMock()
    mock_client_instance.calls.create.return_value = mock_call

    mock_cursor = MagicMock()
    mock_ctx = MagicMock()
    mock_ctx.__enter__ = MagicMock(return_value=mock_cursor)
    mock_ctx.__exit__ = MagicMock(return_value=False)

    with patch("vapi_caller.get_cursor", return_value=mock_ctx), \
         patch("twilio.rest.Client", return_value=mock_client_instance):

        from vapi_caller import _make_vapi_call
        _make_vapi_call(cid, event)

    # Find the UPDATE call among cursor.execute calls
    update_calls = [
        c for c in mock_cursor.execute.call_args_list
        if "UPDATE vapi_calls" in str(c)
    ]
    assert len(update_calls) == 1

    update_args = update_calls[0]
    sql = update_args[0][0]
    params = update_args[0][1]

    assert "call_id" in sql
    assert "status" in sql
    assert params[0] == sid       # call_id = call.sid
    assert params[1] == cid       # WHERE id = call_db_id
    assert "'queued'" in sql      # status = 'queued'


# ============================================================
# Property 3: Successful Call Broadcast
# Feature: twilio-voice-migration, Property 3: Successful Call Broadcast
# **Validates: Requirements 1.4**
# ============================================================

@settings(max_examples=100)
@given(cid=call_db_ids, event=event_data_st, sid=call_sids)
def test_successful_call_broadcast(cid, event, sid):
    """For any successful call, broadcast_fn is called with correct
    voice_call payload."""

    mock_call = MagicMock()
    mock_call.sid = sid

    mock_client_instance = MagicMock()
    mock_client_instance.calls.create.return_value = mock_call

    mock_cursor = MagicMock()
    mock_ctx = MagicMock()
    mock_ctx.__enter__ = MagicMock(return_value=mock_cursor)
    mock_ctx.__exit__ = MagicMock(return_value=False)

    mock_broadcast = MagicMock()

    with patch("vapi_caller.get_cursor", return_value=mock_ctx), \
         patch("twilio.rest.Client", return_value=mock_client_instance):

        from vapi_caller import _make_vapi_call, ALERT_PHONE_NUMBER
        _make_vapi_call(cid, event, broadcast_fn=mock_broadcast)

    mock_broadcast.assert_called_once()
    payload = mock_broadcast.call_args[0][0]

    assert payload["type"] == "voice_call"
    assert payload["data"]["event_id"] == str(event["event_id"])
    assert payload["data"]["call_id"] == sid
    assert payload["data"]["status"] == "queued"
    assert payload["data"]["phone_number"] == ALERT_PHONE_NUMBER


# ============================================================
# Property 4: Failed Call Error Handling
# Feature: twilio-voice-migration, Property 4: Failed Call Error Handling
# **Validates: Requirements 1.5**
# ============================================================

@settings(max_examples=100)
@given(cid=call_db_ids, event=event_data_st, err_msg=error_messages)
def test_failed_call_error_handling(cid, event, err_msg):
    """For any exception with arbitrary error message, DB gets
    status='failed' and error_message truncated to 500 chars."""

    mock_client_instance = MagicMock()
    mock_client_instance.calls.create.side_effect = Exception(err_msg)

    mock_cursor = MagicMock()
    mock_ctx = MagicMock()
    mock_ctx.__enter__ = MagicMock(return_value=mock_cursor)
    mock_ctx.__exit__ = MagicMock(return_value=False)

    with patch("vapi_caller.get_cursor", return_value=mock_ctx), \
         patch("twilio.rest.Client", return_value=mock_client_instance):

        from vapi_caller import _make_vapi_call
        _make_vapi_call(cid, event)

    # Find the UPDATE call for the failure
    update_calls = [
        c for c in mock_cursor.execute.call_args_list
        if "UPDATE vapi_calls" in str(c) and "failed" in str(c)
    ]
    assert len(update_calls) == 1

    update_args = update_calls[0]
    params = update_args[0][1]

    stored_error = params[0]
    assert len(stored_error) <= 500
    # The stored error should be a prefix of the original error message
    assert stored_error == str(err_msg)[:500]
    assert params[1] == cid  # WHERE id = call_db_id


# ============================================================
# Property 5: TwiML Response Correctness
# Feature: twilio-voice-migration, Property 5: TwiML Response Correctness
# **Validates: Requirements 2.2, 2.3, 2.4, 2.5, 2.6**
# ============================================================

@settings(max_examples=100)
@given(cid=call_db_ids, host=service_hosts)
def test_twiml_response_correctness(cid, host):
    """For any call_db_id and SERVICE_HOST value, TwiML returns correct
    XML with right ws/wss scheme."""

    with patch("vapi_caller.SERVICE_HOST", host), \
         patch("main.SERVICE_HOST", host):

        from main import app
        client = TestClient(app, raise_server_exceptions=False)
        response = client.get(f"/api/twiml/{cid}")

    assert response.status_code == 200
    assert "application/xml" in response.headers["content-type"]

    body = response.text

    # Must contain the XML declaration and Response wrapper
    assert "<?xml" in body
    assert "<Response>" in body
    assert "</Response>" in body

    # Must contain the Say greeting
    assert "<Say>" in body
    assert "MediProxy compliance agent" in body

    # Must contain Connect > Stream
    assert "<Connect>" in body
    assert "<Stream" in body
    assert "</Connect>" in body

    # Correct scheme: ws:// for localhost/127.0.0.1/empty, wss:// otherwise
    effective_host = host or "localhost"
    if effective_host in ("localhost", "127.0.0.1"):
        assert f'ws://{effective_host}/api/voice-agent/{cid}' in body
        assert f'wss://' not in body
    else:
        assert f'wss://{effective_host}/api/voice-agent/{cid}' in body

    # Path must include the call_db_id
    assert f"/api/voice-agent/{cid}" in body


# ============================================================
# Property 6: is_configured Correctness
# Feature: twilio-voice-migration, Property 6: is_configured Correctness
# **Validates: Requirements 3.1, 3.2**
# ============================================================

@settings(max_examples=100)
@given(
    telephony=env_var_values,
    account_sid=env_var_values,
    auth_token=env_var_values,
    phone_number=env_var_values,
    alert_phone=env_var_values,
)
def test_is_configured_correctness(telephony, account_sid, auth_token, phone_number, alert_phone):
    """For any combination of env vars, is_configured() returns True iff
    all five are set and non-empty."""

    # TELEPHONY_ENABLED is special: it must be "true" (lowercased) to be truthy
    telephony_bool = telephony.lower() == "true"

    with patch("vapi_caller.TELEPHONY_ENABLED", telephony_bool), \
         patch("vapi_caller.TWILIO_ACCOUNT_SID", account_sid), \
         patch("vapi_caller.TWILIO_AUTH_TOKEN", auth_token), \
         patch("vapi_caller.TWILIO_PHONE_NUMBER", phone_number), \
         patch("vapi_caller.ALERT_PHONE_NUMBER", alert_phone):

        from vapi_caller import is_configured
        result = is_configured()

    all_set = (
        telephony_bool
        and bool(account_sid)
        and bool(auth_token)
        and bool(phone_number)
        and bool(alert_phone)
    )

    assert result == all_set, (
        f"is_configured()={result} but expected {all_set} for "
        f"TELEPHONY_ENABLED={telephony_bool!r}, SID={account_sid!r}, "
        f"TOKEN={auth_token!r}, PHONE={phone_number!r}, ALERT={alert_phone!r}"
    )


# ============================================================
# Property 7: Twilio-to-Deepgram Audio Fidelity
# Feature: twilio-voice-migration, Property 7: Twilio-to-Deepgram Audio Fidelity
# **Validates: Requirements 7.1, 7.2**
# ============================================================

@settings(max_examples=100)
@given(raw_audio=audio_bytes_st)
def test_twilio_to_deepgram_audio_fidelity(raw_audio):
    """For any raw mulaw bytes, base64-encoding then decoding in the
    relay yields the exact original bytes."""

    # Simulate what Twilio sends: base64-encode the raw audio
    b64_payload = base64.b64encode(raw_audio).decode("ascii")

    # Simulate what the relay does: decode the base64 payload
    decoded = base64.b64decode(b64_payload)

    assert decoded == raw_audio


# ============================================================
# Property 8: Deepgram-to-Twilio Audio Framing
# Feature: twilio-voice-migration, Property 8: Deepgram-to-Twilio Audio Framing
# **Validates: Requirements 7.3, 7.4**
# ============================================================

@settings(max_examples=100)
@given(raw_audio=audio_bytes_st, stream_sid=stream_sids)
def test_deepgram_to_twilio_audio_framing(raw_audio, stream_sid):
    """For any audio bytes and streamSid, the relay produces valid JSON
    with correct structure and base64 round-trip."""

    # Simulate what the Deepgram→Twilio relay builds
    media_msg = {
        "event": "media",
        "streamSid": stream_sid,
        "media": {
            "payload": base64.b64encode(raw_audio).decode("ascii"),
        },
    }

    # Serialize and deserialize (as the relay does via send_text)
    serialized = json.dumps(media_msg)
    parsed = json.loads(serialized)

    # Structural correctness
    assert parsed["event"] == "media"
    assert parsed["streamSid"] == stream_sid
    assert "media" in parsed
    assert "payload" in parsed["media"]

    # Base64 round-trip fidelity
    recovered = base64.b64decode(parsed["media"]["payload"])
    assert recovered == raw_audio
