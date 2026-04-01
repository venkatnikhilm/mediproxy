# Implementation Plan: Twilio Voice Migration

## Overview

Migrate the ShadowGuard outbound telephony from Amazon Connect (boto3) to Twilio (`client.calls.create()` + Media Streams). The implementation proceeds bottom-up: dependencies and env config first, then the caller module, then the TwiML endpoint, then the bridge relay refactor, and finally tests.

## Tasks

- [x] 1. Update dependencies and environment configuration
  - [x] 1.1 Replace `boto3` with `twilio` in `backend/requirements.txt`
    - Remove the `boto3==1.35.0` line
    - Add `twilio>=8.0.0`
    - Keep all other dependencies unchanged
    - _Requirements: 5.1, 5.2, 5.3_

  - [x] 1.2 Migrate `.env` from AWS Connect to Twilio credentials
    - Remove `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`, `CONNECT_INSTANCE_ID`, `CONNECT_CONTACT_FLOW_ID`, `CONNECT_SOURCE_PHONE`
    - Add `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER` with placeholder values
    - Retain `TELEPHONY_ENABLED`, `ALERT_PHONE_NUMBER`, `CALL_COOLDOWN_SECONDS`, `DEEPGRAM_API_KEY`, `SERVICE_HOST` unchanged
    - Update the comment header to reference Twilio instead of Amazon Connect
    - _Requirements: 4.1, 4.2, 4.3_

- [x] 2. Rewrite `vapi_caller.py` for Twilio
  - [x] 2.1 Replace constants and imports in `backend/vapi_caller.py`
    - Remove `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`, `CONNECT_INSTANCE_ID`, `CONNECT_CONTACT_FLOW_ID`, `CONNECT_SOURCE_PHONE` constants
    - Remove `_get_connect_client()` function and `boto3` import
    - Add `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER` constants from env vars
    - Update module docstring to reference Twilio instead of Amazon Connect
    - _Requirements: 1.6, 3.3_

  - [x] 2.2 Update `is_configured()` to check Twilio env vars
    - Return `True` only when `TELEPHONY_ENABLED` is true and `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER`, `ALERT_PHONE_NUMBER` are all non-empty
    - Remove all AWS credential checks
    - _Requirements: 3.1, 3.2_

  - [x] 2.3 Rewrite `_make_vapi_call` to use Twilio `client.calls.create()`
    - Retain the same signature: `_make_vapi_call(call_db_id: int, event_data: dict, broadcast_fn=None)`
    - Construct TwiML URL: `http(s)://{SERVICE_HOST}/api/twiml/{call_db_id}` (http for localhost/127.0.0.1, https otherwise)
    - Create Twilio Client with `TWILIO_ACCOUNT_SID` and `TWILIO_AUTH_TOKEN`
    - Call `client.calls.create(to=ALERT_PHONE_NUMBER, from_=TWILIO_PHONE_NUMBER, url=twiml_url)`
    - On success: update `vapi_calls` with `call_id = call.sid`, `status = 'queued'`, broadcast via `broadcast_fn`
    - On failure: update `vapi_calls` with `status = 'failed'`, `error_message` truncated to 500 chars
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [ ] 3. Checkpoint — Verify caller module compiles
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Add TwiML endpoint and update bridge relay in `backend/main.py`
  - [x] 4.1 Add `GET /api/twiml/{call_db_id}` TwiML endpoint
    - Import `Response` from `fastapi.responses` and `SERVICE_HOST` from `vapi_caller`
    - Return XML with `Content-Type: application/xml`
    - XML contains `<Say>` greeting ("Please hold, connecting you to the ShadowGuard compliance agent.") followed by `<Connect><Stream url="..."/>`
    - Use `ws://` scheme when `SERVICE_HOST` is `localhost`, `127.0.0.1`, or empty; `wss://` otherwise
    - Fall back to `localhost` when `SERVICE_HOST` is empty
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6_

  - [x] 4.2 Refactor `_relay_connect_to_deepgram` → `_relay_twilio_to_deepgram`
    - Accept a shared `state` dict parameter to store `streamSid`
    - Receive JSON text messages from Twilio via `websocket.receive_text()`
    - On `start` event: extract `streamSid` from `msg["start"]["streamSid"]` and store in `state["stream_sid"]`
    - On `media` event: base64-decode `msg["media"]["payload"]` and forward raw bytes to Deepgram via `deepgram_ws.send()`
    - On `stop` event: break the relay loop
    - Skip invalid JSON with a log warning
    - _Requirements: 7.1, 7.2, 7.4, 7.5_

  - [x] 4.3 Refactor `_relay_deepgram_to_connect` → `_relay_deepgram_to_twilio`
    - Accept a shared `state` dict parameter to read `stream_sid`
    - When Deepgram sends binary audio: base64-encode and wrap in Twilio Media Stream JSON `{"event":"media","streamSid":"...","media":{"payload":"..."}}`
    - Send via `websocket.send_text(json.dumps(msg))` instead of `send_bytes`
    - JSON control messages from Deepgram (FunctionCallRequest) handled identically to before
    - _Requirements: 7.3, 7.4_

  - [x] 4.4 Update `voice_agent_bridge` to use new relay functions
    - Create shared `state = {"stream_sid": None}` dict
    - Pass `state` to both `_relay_twilio_to_deepgram` and `_relay_deepgram_to_twilio`
    - Update task creation to use the renamed relay functions
    - Update the `trigger_test_call` endpoint error message to reference Twilio instead of AWS Connect
    - _Requirements: 6.1, 7.4_

- [x] 5. Update test fixtures in `backend/tests/conftest.py`
  - Replace `boto3` mock with `twilio` mock so importing `vapi_caller` doesn't hit real Twilio client
  - Keep `psycopg2` mock unchanged
  - _Requirements: 6.2, 6.5_

- [x] 6. Checkpoint — Verify all existing tests still pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Update unit tests in `backend/tests/test_voice_agent_unit.py`
  - [x] 7.1 Add TwiML endpoint unit tests
    - `test_twiml_endpoint_registered` — GET `/api/twiml/1` returns 200
    - `test_twiml_content_type` — response has `Content-Type: application/xml`
    - `test_twiml_contains_say_and_stream` — XML contains `<Say>` greeting and `<Stream>` element
    - _Requirements: 2.1, 2.2, 2.3_

  - [x] 7.2 Update existing bridge and caller tests for Twilio
    - `test_bridge_endpoint_registered` — verify WS route still exists (unchanged)
    - Update `test_missing_api_key_closes_1008` if any import paths changed
    - Add `test_make_vapi_call_signature_unchanged` — verify function accepts `(call_db_id, event_data, broadcast_fn)`
    - _Requirements: 1.1, 6.1_

- [x] 8. Add property-based tests in `backend/tests/test_twilio_migration_properties.py`
  - [ ]* 8.1 Write property test for Twilio call creation correctness
    - **Property 1: Twilio Call Creation Correctness**
    - For any `call_db_id` and `event_data`, `_make_vapi_call` calls `client.calls.create()` with correct `to`, `from_`, and `url` args
    - **Validates: Requirements 1.2**

  - [ ]* 8.2 Write property test for successful call DB update
    - **Property 2: Successful Call DB Update**
    - For any Call SID returned by Twilio, the DB record is updated with that SID and status `'queued'`
    - **Validates: Requirements 1.3**

  - [ ]* 8.3 Write property test for successful call broadcast
    - **Property 3: Successful Call Broadcast**
    - For any successful call, `broadcast_fn` is called with correct `voice_call` payload
    - **Validates: Requirements 1.4**

  - [ ]* 8.4 Write property test for failed call error handling
    - **Property 4: Failed Call Error Handling**
    - For any exception with arbitrary error message, DB gets `status='failed'` and `error_message` truncated to 500 chars
    - **Validates: Requirements 1.5**

  - [ ]* 8.5 Write property test for TwiML response correctness
    - **Property 5: TwiML Response Correctness**
    - For any `call_db_id` and `SERVICE_HOST` value, TwiML returns correct XML with right ws/wss scheme
    - **Validates: Requirements 2.2, 2.3, 2.4, 2.5, 2.6**

  - [ ]* 8.6 Write property test for `is_configured` correctness
    - **Property 6: `is_configured` Correctness**
    - For any combination of env vars, `is_configured()` returns `True` iff all five are set and non-empty
    - **Validates: Requirements 3.1, 3.2**

  - [ ]* 8.7 Write property test for Twilio-to-Deepgram audio fidelity
    - **Property 7: Twilio-to-Deepgram Audio Fidelity**
    - For any raw mulaw bytes, base64-encoding then decoding in the relay yields the exact original bytes
    - **Validates: Requirements 7.1, 7.2**

  - [ ]* 8.8 Write property test for Deepgram-to-Twilio audio framing
    - **Property 8: Deepgram-to-Twilio Audio Framing**
    - For any audio bytes and `streamSid`, the relay produces valid JSON with correct structure and base64 round-trip
    - **Validates: Requirements 7.3, 7.4**

- [x] 9. Final checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples and edge cases
- `deepgram_agent.py`, `database.py`, and `models.py` are intentionally not modified (Requirement 6)
