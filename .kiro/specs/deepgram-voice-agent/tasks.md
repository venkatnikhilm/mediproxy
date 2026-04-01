# Implementation Plan: Deepgram Voice Agent

## Overview

Replace the static Amazon Connect + Polly alert call with a conversational Deepgram Voice Agent. The implementation adds a WebSocket bridge endpoint to `main.py`, a new `deepgram_agent.py` module for Deepgram connection/configuration helpers, updates `_make_vapi_call` in `vapi_caller.py`, and adds comprehensive tests. All existing cooldown, DB tracking, and broadcast infrastructure remain untouched.

## Tasks

- [x] 1. Create Deepgram agent helper module
  - [x] 1.1 Create `backend/deepgram_agent.py` with settings configuration builder
    - Implement `build_settings(event_data: dict) -> dict` that returns the `SettingsConfiguration` message with `mulaw` 8kHz audio config, `nova-2` listen model, `gpt-4o-mini` think model, `aura-asteria-en` speak model
    - Implement `_build_system_prompt(event_data: dict) -> str` that injects `ai_service`, `phi_types`, `risk_score`, `severity`, `source_ip`, `redacted_text`, `timestamp` into the prompt
    - System prompt must: identify as "ShadowGuard compliance assistant", lead with `ai_service`/`phi_types`/`risk_score`, ask before elaborating, limit to 1–3 sentences, avoid markdown/bullet points, instruct confirmation before status actions
    - Define `MITIGATE_FUNCTION_DEF` and `RESOLVE_FUNCTION_DEF` function definitions for Deepgram tool calling
    - Implement `connect_to_deepgram(api_key: str) -> websockets.WebSocketClientProtocol` async helper that opens `wss://agent.deepgram.com/agent` with `Authorization: Token {api_key}` header
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 3.1, 4.1, 7.1_

  - [ ]* 1.2 Write property test for system prompt completeness (Property 4)
    - **Property 4: System Prompt Completeness**
    - Generate arbitrary PHI event dicts with Hypothesis; verify `_build_system_prompt` output contains all required fields and instructions
    - **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6**

  - [ ]* 1.3 Write property test for status action confirmation in prompt (Property 5)
    - **Property 5: Status Action Requires Confirmation**
    - Verify system prompt always contains confirmation instructions for mitigate and resolve actions
    - **Validates: Requirements 3.1, 4.1**

- [x] 2. Implement WebSocket bridge endpoint
  - [x] 2.1 Add `/api/voice-agent/{call_db_id}` WebSocket route to `main.py`
    - Accept Connect WebSocket, validate `DEEPGRAM_API_KEY` env var (close with 1008 if missing)
    - Fetch PHI event data from DB via `call_db_id` → `event_id` join on `vapi_calls`
    - Open Deepgram Voice Agent WebSocket using `connect_to_deepgram`
    - Send `SettingsConfiguration` message via `build_settings(event_data)`
    - Run two concurrent async tasks: Connect→Deepgram audio relay and Deepgram→Connect audio relay
    - Forward audio bytes bidirectionally without modification
    - Track session start time for duration calculation
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 7.1, 7.2_

  - [x] 2.2 Implement Deepgram function call handling in the bridge endpoint
    - Parse incoming Deepgram JSON messages for `FunctionCallRequest` type
    - On `mark_mitigated`: call `PATCH /api/events/{event_id}/status` with `{"status": "mitigated"}`
    - On `mark_resolved`: call `PATCH /api/events/{event_id}/status` with `{"status": "resolved"}`
    - On success: send `FunctionCallResponse` back to Deepgram, invoke `broadcast_from_thread` with `status_update` message
    - On failure: send `FunctionCallResponse` with error text so agent informs officer to update manually
    - _Requirements: 3.2, 3.3, 3.4, 3.5, 4.2, 4.3, 4.4, 4.5_

  - [x] 2.3 Implement call finalization logic in the bridge endpoint
    - On normal session end: update `vapi_calls` record with `status='completed'`, `ended_at=<UTC>`, `duration_seconds=<elapsed>`
    - On error/unexpected disconnect: update `vapi_calls` record with `status='failed'`, `ended_at=<UTC>`
    - Ensure both WebSocket connections are closed cleanly on any termination path
    - Log all errors under `shadowguard.voice_agent` logger
    - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [ ] 3. Checkpoint - Ensure bridge endpoint is complete
  - Ensure all tests pass, ask the user if questions arise.

- [-] 4. Update `_make_vapi_call` in `vapi_caller.py`
  - [x] 4.1 Modify `_make_vapi_call` to route calls to the bridge endpoint
    - Keep the same function signature: `_make_vapi_call(call_db_id: int, event_data: dict, broadcast_fn=None)`
    - Construct bridge WebSocket URL: `wss://{SERVICE_HOST}/api/voice-agent/{call_db_id}`
    - Pass `bridge_url` and full event data (`event_id`, `ai_service`, `phi_types`, `risk_score`, `severity`, `source_ip`, `redacted_text`, `timestamp`) as `Attributes` to `start_outbound_voice_contact`
    - Read `SERVICE_HOST` from env var, fall back to `localhost`
    - Add `DEEPGRAM_API_KEY` to the `is_configured()` check is NOT required (keep existing checks unchanged per Req 6.4)
    - Leave `maybe_trigger_call`, cooldown logic, and all other functions unchanged
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 7.3_

  - [ ]* 4.2 Write property test for `_make_vapi_call` triggers Connect call (Property 9)
    - **Property 9: `_make_vapi_call` Triggers Connect Outbound Call**
    - Mock boto3 client; verify `start_outbound_voice_contact` called exactly once with correct phone numbers for any `call_db_id`/`event_data`
    - **Validates: Requirements 6.2**

  - [ ]* 4.3 Write property test for `_make_vapi_call` passes full event data (Property 10)
    - **Property 10: `_make_vapi_call` Passes Full Event Data**
    - Generate arbitrary event_data dicts; verify all required fields present in `Attributes` passed to `start_outbound_voice_contact`
    - **Validates: Requirements 6.3**

- [ ] 5. Checkpoint - Ensure vapi_caller changes are correct
  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. Add environment configuration and wiring
  - [x] 6.1 Update `.env` with `DEEPGRAM_API_KEY` placeholder and optional `SERVICE_HOST`
    - Add `DEEPGRAM_API_KEY=` and `SERVICE_HOST=` entries
    - _Requirements: 7.1, 7.2_

  - [x] 6.2 Update `backend/requirements.txt` with new dependencies
    - Add `websockets` package for Deepgram WebSocket client connection
    - _Requirements: 1.2_

- [x] 7. Write unit and integration tests
  - [x] 7.1 Create `backend/tests/test_voice_agent_unit.py` with unit tests
    - `test_bridge_endpoint_registered` — verify `/api/voice-agent/1` route exists
    - `test_missing_api_key_closes_1008` — with `DEEPGRAM_API_KEY` unset, connection closes with code 1008
    - `test_system_prompt_contains_identity` — known event produces prompt with "ShadowGuard compliance assistant"
    - `test_patch_failure_returns_error_response` — mock PATCH returning 500, verify error handling
    - `test_build_settings_audio_config` — verify mulaw 8kHz audio encoding in settings
    - _Requirements: 1.5, 2.2, 7.2_

  - [ ]* 7.2 Create `backend/tests/test_voice_agent_properties.py` with remaining property tests
    - **Property 1: Audio Relay Fidelity** — arbitrary bytes forwarded unchanged in both directions
    - **Validates: Requirements 1.3, 1.4**
    - **Property 2: Deepgram Connection Uses API Key** — any connection uses the env var value
    - **Validates: Requirements 1.2, 7.1**
    - **Property 3: WebSocket Cleanup on Either Side Close** — closing either side closes the other
    - **Validates: Requirements 1.6, 5.4**
    - **Property 6: Status Action PATCH Correctness** — any event_id + action → correct PATCH body
    - **Validates: Requirements 3.2, 4.2**
    - **Property 7: Broadcast on Successful Status Update** — any successful update → broadcast called once with correct payload
    - **Validates: Requirements 3.4, 4.4**
    - **Property 8: Call Finalization Correctness** — any session duration → correct DB fields written
    - **Validates: Requirements 5.2, 5.3**

- [ ] 8. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples and edge cases
- The only new required environment variable is `DEEPGRAM_API_KEY`; `SERVICE_HOST` is optional
