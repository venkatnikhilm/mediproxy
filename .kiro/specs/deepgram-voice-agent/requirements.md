# Requirements Document

## Introduction

Replace the static one-way Amazon Connect + Polly alert call in `vapi_caller.py` with a conversational voice AI agent powered by Deepgram's Voice Agent API. When a high-risk PHI exposure event is detected, AWS Connect still places the outbound call, but the audio is bridged to a new FastAPI WebSocket endpoint that connects to Deepgram's Voice Agent. The compliance officer can then have a real back-and-forth conversation with the ShadowGuard agent — asking questions about the event, requesting details, and verbally triggering status changes (mitigate or resolve) — rather than listening to a static announcement.

## Glossary

- **Voice_Agent**: The Deepgram-powered conversational AI component that handles the two-way audio session with the compliance officer.
- **Bridge_Endpoint**: The FastAPI WebSocket endpoint (`/api/voice-agent/{call_db_id}`) that relays audio between AWS Connect and the Deepgram Voice Agent API.
- **Deepgram_API**: Deepgram's Voice Agent WebSocket API used for real-time speech-to-text, LLM reasoning, and text-to-speech.
- **Connect_Client**: The AWS Connect service that places the outbound call to the compliance officer's phone.
- **Compliance_Officer**: The human recipient of the alert call who interacts with the Voice_Agent.
- **PHI_Event**: A detected high-risk protected health information exposure event stored in the `events` table.
- **Status_Action**: A verbal command from the Compliance_Officer to change a PHI_Event's status to "mitigated" or "resolved".
- **Broadcast_Fn**: The `broadcast_from_thread` helper in `main.py` used to push WebSocket messages to dashboard clients.
- **vapi_calls**: The PostgreSQL table tracking outbound call records including status, duration, and timestamps.

---

## Requirements

### Requirement 1: WebSocket Bridge Endpoint

**User Story:** As a system operator, I want a FastAPI WebSocket endpoint that bridges AWS Connect audio to Deepgram's Voice Agent API, so that the compliance officer's phone call is handled by a conversational AI rather than a static Polly announcement.

#### Acceptance Criteria

1. THE Bridge_Endpoint SHALL accept WebSocket connections at the path `/api/voice-agent/{call_db_id}`.
2. WHEN a WebSocket connection is established at the Bridge_Endpoint, THE Bridge_Endpoint SHALL open a corresponding WebSocket connection to the Deepgram_API using the `DEEPGRAM_API_KEY` environment variable.
3. WHEN audio bytes are received from the Connect_Client over the Bridge_Endpoint WebSocket, THE Bridge_Endpoint SHALL forward those bytes to the Deepgram_API WebSocket without modification.
4. WHEN audio bytes are received from the Deepgram_API, THE Bridge_Endpoint SHALL forward those bytes to the Connect_Client WebSocket without modification.
5. IF the `DEEPGRAM_API_KEY` environment variable is not set, THEN THE Bridge_Endpoint SHALL close the WebSocket connection with a 1008 (Policy Violation) status code and log an error.
6. WHEN either the Connect_Client or the Deepgram_API WebSocket closes, THE Bridge_Endpoint SHALL close the other connection and proceed to call finalization.

---

### Requirement 2: Voice Agent Initialization

**User Story:** As a compliance officer, I want the voice agent to be initialized with full context about the PHI event before the call begins, so that I receive relevant, accurate information immediately.

#### Acceptance Criteria

1. WHEN the Deepgram_API connection is established, THE Voice_Agent SHALL be configured with a system prompt that includes: `ai_service`, `phi_types`, `risk_score`, `severity`, `source_ip`, `redacted_text`, and `timestamp` from the PHI_Event.
2. THE Voice_Agent SHALL identify itself as "ShadowGuard compliance assistant" in its opening statement.
3. THE Voice_Agent SHALL lead its opening statement with the most critical facts: `ai_service`, `phi_types`, and `risk_score`.
4. THE Voice_Agent SHALL ask the Compliance_Officer if they want more detail before providing the full event context.
5. THE Voice_Agent SHALL limit each spoken response to 1–3 sentences.
6. THE Voice_Agent SHALL use a conversational tone appropriate for spoken audio, avoiding markdown, bullet points, or written formatting in its responses.

---

### Requirement 3: Status Action — Mitigate

**User Story:** As a compliance officer, I want to verbally mark a PHI event as mitigated during the call, so that I can take action without switching to the dashboard.

#### Acceptance Criteria

1. WHEN the Compliance_Officer verbally requests to mark the event as mitigated, THE Voice_Agent SHALL ask for confirmation before taking action (e.g., "Shall I mark this as mitigated?").
2. WHEN the Compliance_Officer confirms the mitigate action, THE Voice_Agent SHALL call `PATCH /api/events/{event_id}/status` with `{"status": "mitigated"}`.
3. WHEN the status update to "mitigated" succeeds, THE Voice_Agent SHALL verbally confirm the action to the Compliance_Officer.
4. WHEN the status update to "mitigated" succeeds, THE Bridge_Endpoint SHALL invoke Broadcast_Fn with a message of type `"status_update"` containing the `event_id` and new status.
5. IF the `PATCH /api/events/{event_id}/status` request fails, THEN THE Voice_Agent SHALL inform the Compliance_Officer that the action could not be completed and suggest they update the status manually on the dashboard.

---

### Requirement 4: Status Action — Resolve

**User Story:** As a compliance officer, I want to verbally mark a PHI event as resolved during the call, so that I can close out the alert without switching to the dashboard.

#### Acceptance Criteria

1. WHEN the Compliance_Officer verbally requests to mark the event as resolved, THE Voice_Agent SHALL ask for confirmation before taking action (e.g., "Shall I mark this as resolved?").
2. WHEN the Compliance_Officer confirms the resolve action, THE Voice_Agent SHALL call `PATCH /api/events/{event_id}/status` with `{"status": "resolved"}`.
3. WHEN the status update to "resolved" succeeds, THE Voice_Agent SHALL verbally confirm the action to the Compliance_Officer.
4. WHEN the status update to "resolved" succeeds, THE Bridge_Endpoint SHALL invoke Broadcast_Fn with a message of type `"status_update"` containing the `event_id` and new status.
5. IF the `PATCH /api/events/{event_id}/status` request fails, THEN THE Voice_Agent SHALL inform the Compliance_Officer that the action could not be completed and suggest they update the status manually on the dashboard.

---

### Requirement 5: Graceful Call Termination

**User Story:** As a compliance officer, I want the call to end gracefully once I've resolved or dismissed the alert, so that the interaction feels complete and the system records are accurate.

#### Acceptance Criteria

1. WHEN the Compliance_Officer verbally dismisses or resolves the alert, THE Voice_Agent SHALL deliver a closing statement and signal the end of the conversation.
2. WHEN the call session ends (WebSocket closes), THE Bridge_Endpoint SHALL update the `vapi_calls` record identified by `call_db_id` with: `status = 'completed'`, `ended_at = <UTC timestamp>`, and `duration_seconds = <elapsed seconds since connection opened>`.
3. IF the call ends due to an error or unexpected disconnect, THEN THE Bridge_Endpoint SHALL update the `vapi_calls` record with `status = 'failed'` and `ended_at = <UTC timestamp>`.
4. WHEN the call session ends, THE Bridge_Endpoint SHALL close all open WebSocket connections cleanly.

---

### Requirement 6: Replace `_make_vapi_call` in `vapi_caller.py`

**User Story:** As a developer, I want `_make_vapi_call` updated to route the call audio to the new Bridge_Endpoint instead of a Polly contact flow, so that the conversational agent is used for all future alert calls.

#### Acceptance Criteria

1. THE updated `_make_vapi_call` function SHALL use the same signature: `_make_vapi_call(call_db_id: int, event_data: dict, broadcast_fn=None)`.
2. WHEN `_make_vapi_call` is called, THE Connect_Client SHALL place an outbound call via `start_outbound_voice_contact` using a contact flow configured to stream audio to the Bridge_Endpoint WebSocket URL.
3. THE updated `_make_vapi_call` SHALL pass the full `event_data` dict (including `event_id`, `ai_service`, `phi_types`, `risk_score`, `severity`, `source_ip`, `redacted_text`, `timestamp`) to the Bridge_Endpoint so the Voice_Agent can be initialized with complete context.
4. THE `maybe_trigger_call`, cooldown logic, DB tracking, and all other functions in `vapi_caller.py` SHALL remain unchanged.
5. THE `DEEPGRAM_API_KEY` environment variable SHALL be the only new required environment variable introduced by this feature.

---

### Requirement 7: Environment Configuration

**User Story:** As a system operator, I want the Deepgram integration to be configured via environment variables, so that credentials are not hardcoded and the system is easy to configure across environments.

#### Acceptance Criteria

1. THE Voice_Agent SHALL read the Deepgram API key exclusively from the `DEEPGRAM_API_KEY` environment variable.
2. IF `DEEPGRAM_API_KEY` is not set or is empty, THEN THE Bridge_Endpoint SHALL log an error and refuse to establish a Deepgram_API connection.
3. THE system SHALL NOT require any new AWS environment variables beyond those already defined in `vapi_caller.py`.
