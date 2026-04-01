# Requirements Document

## Introduction

Migrate the outbound telephony provider in `vapi_caller.py` from Amazon Connect (via `boto3` `start_outbound_voice_contact`) to Twilio (via `twilio` REST API `client.calls.create()`). The motivation is that AWS Connect cannot natively stream bidirectional audio to a WebSocket — it requires Kinesis Video Streams and Lambda plumbing — whereas Twilio Media Streams natively support bidirectional WebSocket audio via `<Connect><Stream>` TwiML.

The Deepgram Voice Agent bridge endpoint (`/api/voice-agent/{call_db_id}`) retains its WebSocket path and Deepgram integration, but its internal message handling must be updated to support Twilio Media Stream JSON framing (base64-encoded mulaw audio wrapped in JSON `media` events). Deepgram connection, function calling, DB tracking (`vapi_calls` table), cooldown logic, and dashboard broadcast infrastructure all remain unchanged.

Twilio sends mulaw 8 kHz audio by default, which matches the existing Deepgram audio configuration — no audio encoding changes are needed.

## Glossary

- **Twilio_Client**: The Twilio REST API client used to place outbound calls via `client.calls.create()`.
- **TwiML_Endpoint**: A new HTTP GET endpoint in `main.py` that returns TwiML XML instructing Twilio to open a Media Stream WebSocket to the Bridge_Endpoint.
- **Bridge_Endpoint**: The existing FastAPI WebSocket endpoint (`/api/voice-agent/{call_db_id}`) that relays audio between the telephony provider and the Deepgram Voice Agent API.
- **Media_Stream**: Twilio's bidirectional WebSocket audio streaming feature, activated via `<Connect><Stream>` TwiML.
- **Compliance_Officer**: The human recipient of the alert call who interacts with the voice agent.
- **PHI_Event**: A detected high-risk protected health information exposure event stored in the `events` table.
- **vapi_calls**: The PostgreSQL table tracking outbound call records including status, duration, and timestamps.
- **Broadcast_Fn**: The `broadcast_from_thread` helper in `main.py` used to push WebSocket messages to dashboard clients.

---

## Requirements

### Requirement 1: Replace `_make_vapi_call` with Twilio Call Creation

**User Story:** As a system operator, I want `_make_vapi_call` to place outbound calls via the Twilio REST API instead of Amazon Connect, so that the telephony provider natively supports bidirectional WebSocket audio streaming without additional AWS infrastructure.

#### Acceptance Criteria

1. THE updated `_make_vapi_call` function SHALL retain the same signature: `_make_vapi_call(call_db_id: int, event_data: dict, broadcast_fn=None)`.
2. WHEN `_make_vapi_call` is called, THE Twilio_Client SHALL place an outbound call via `client.calls.create()` with `to` set to `ALERT_PHONE_NUMBER`, `from_` set to `TWILIO_PHONE_NUMBER`, and `url` set to the TwiML_Endpoint URL for the given `call_db_id`.
3. WHEN the Twilio call is successfully created, THE `_make_vapi_call` function SHALL update the `vapi_calls` record with the Twilio Call SID as `call_id` and set `status` to `'queued'`.
4. WHEN the Twilio call is successfully created, THE `_make_vapi_call` function SHALL invoke `broadcast_fn` with a message of type `"voice_call"` containing the `event_id`, Twilio Call SID, status `"queued"`, and `phone_number`.
5. IF the Twilio call creation fails, THEN THE `_make_vapi_call` function SHALL update the `vapi_calls` record with `status = 'failed'` and store the error message (truncated to 500 characters).
6. THE `_make_vapi_call` function SHALL remove all references to `boto3`, `_get_connect_client`, `CONNECT_INSTANCE_ID`, `CONNECT_CONTACT_FLOW_ID`, and `CONNECT_SOURCE_PHONE`.

---

### Requirement 2: TwiML Endpoint

**User Story:** As a system operator, I want a TwiML endpoint that instructs Twilio to stream call audio to the existing bridge WebSocket, so that Twilio Media Streams connect to the Deepgram voice agent without additional middleware.

#### Acceptance Criteria

1. THE TwiML_Endpoint SHALL be accessible at `GET /api/twiml/{call_db_id}`.
2. WHEN Twilio requests the TwiML_Endpoint, THE TwiML_Endpoint SHALL return an XML response with `Content-Type: application/xml`.
3. THE TwiML_Endpoint SHALL return a `<Response>` containing a `<Say>` element with the text "Please hold, connecting you to the ShadowGuard compliance agent." followed by a `<Connect>` element with a `<Stream>` element whose `url` attribute points to the Bridge_Endpoint WebSocket URL.
6. WHEN constructing the `<Stream>` URL, THE TwiML_Endpoint SHALL use `wss://` as the scheme, EXCEPT when `SERVICE_HOST` is `localhost` or `127.0.0.1`, in which case the scheme SHALL be `ws://`.
4. THE TwiML_Endpoint SHALL construct the TwiML_Endpoint URL used by `_make_vapi_call` using the `SERVICE_HOST` environment variable for the hostname.
5. IF `SERVICE_HOST` is not set or is empty, THEN THE TwiML_Endpoint SHALL fall back to `localhost` for URL construction.

---

### Requirement 3: Update `is_configured()` for Twilio

**User Story:** As a system operator, I want the telephony configuration check to validate Twilio credentials instead of AWS Connect credentials, so that the system correctly reports whether outbound calling is available.

#### Acceptance Criteria

1. THE `is_configured` function SHALL return `True` only when `TELEPHONY_ENABLED` is `"true"` and `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER`, and `ALERT_PHONE_NUMBER` are all set and non-empty.
2. THE `is_configured` function SHALL return `False` when any of `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER`, or `ALERT_PHONE_NUMBER` is missing or empty.
3. THE `is_configured` function SHALL NOT reference `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `CONNECT_INSTANCE_ID`, `CONNECT_CONTACT_FLOW_ID`, or `CONNECT_SOURCE_PHONE`.

---

### Requirement 4: Environment Variable Migration

**User Story:** As a system operator, I want the `.env` file updated to use Twilio credentials instead of AWS Connect credentials, so that the deployment configuration reflects the new telephony provider.

#### Acceptance Criteria

1. THE `.env` file SHALL contain `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, and `TWILIO_PHONE_NUMBER` as new environment variables with placeholder values.
2. THE `.env` file SHALL remove `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`, `CONNECT_INSTANCE_ID`, `CONNECT_CONTACT_FLOW_ID`, and `CONNECT_SOURCE_PHONE`.
3. THE `.env` file SHALL retain `TELEPHONY_ENABLED`, `ALERT_PHONE_NUMBER`, `CALL_COOLDOWN_SECONDS`, `DEEPGRAM_API_KEY`, and `SERVICE_HOST` unchanged.

---

### Requirement 5: Dependency Migration

**User Story:** As a developer, I want `backend/requirements.txt` updated to use the `twilio` package instead of `boto3`, so that the project dependencies match the new telephony provider.

#### Acceptance Criteria

1. THE `backend/requirements.txt` file SHALL include the `twilio` package with version `>=8.0.0` to ensure compatibility with the current Twilio Python SDK.
2. THE `backend/requirements.txt` file SHALL remove the `boto3` package only if it is not referenced by any other module outside of `vapi_caller.py`.
3. THE `backend/requirements.txt` file SHALL retain all other existing dependencies unchanged.

---

### Requirement 6: Preserve Existing Infrastructure

**User Story:** As a developer, I want all non-telephony components to remain unchanged, so that the Deepgram voice agent, database tracking, cooldown logic, and dashboard broadcasts continue to work without modification.

#### Acceptance Criteria

1. THE Bridge_Endpoint at `/api/voice-agent/{call_db_id}` SHALL retain its existing WebSocket path and external interface, but its internal message handling SHALL be updated to support Twilio Media Stream JSON framing per Requirement 7.
2. THE `deepgram_agent.py` module SHALL remain unchanged.
3. THE `maybe_trigger_call` function, cooldown logic (`_check_cooldown`), and `_extract_phi_list` helper in `vapi_caller.py` SHALL remain unchanged.
4. THE `vapi_calls` database table schema SHALL remain unchanged.
5. THE `database.py` and `models.py` modules SHALL remain unchanged.
6. THE Deepgram audio configuration (mulaw 8 kHz) SHALL remain unchanged, as Twilio Media Streams send mulaw 8 kHz audio by default.

---

### Requirement 7: Twilio Media Stream Audio Compatibility

**User Story:** As a system operator, I want Twilio Media Stream audio to be compatible with the existing Deepgram configuration, so that the voice agent works without audio encoding changes.

#### Acceptance Criteria

1. THE Bridge_Endpoint SHALL accept Twilio Media Stream WebSocket messages, which use JSON framing with base64-encoded mulaw audio in `media` events.
2. WHEN a Twilio Media Stream `media` event is received, THE Bridge_Endpoint SHALL decode the base64 audio payload and forward the raw mulaw bytes to the Deepgram WebSocket.
3. WHEN audio bytes are received from the Deepgram WebSocket, THE Bridge_Endpoint SHALL encode the bytes as base64 and send them back to Twilio in the Media Stream JSON `media` message format, including the `streamSid` extracted from the `start` event in all outbound media messages.
4. WHEN a Twilio Media Stream `start` event is received, THE Bridge_Endpoint SHALL extract the `streamSid` for use in outbound media messages.
5. WHEN a Twilio Media Stream `stop` event is received, THE Bridge_Endpoint SHALL proceed to call finalization.
