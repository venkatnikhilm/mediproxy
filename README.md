# MediProxy AI

**Healthcare AI Security & PHI Protection System**

MediProxy AI intercepts HTTPS traffic to AI services (ChatGPT, Claude, Gemini, DeepSeek, and more), detects Protected Health Information (PHI) using NLP, redacts it in real-time, and provides a cybersecurity-themed governance dashboard with live WebSocket updates. When high-risk PHI exposure is detected, MediProxy automatically calls a compliance officer via Twilio and connects them to a Deepgram-powered AI voice agent that briefs them on the incident and can update event status via voice commands.

---

## Architecture

```
                    ┌──────────────┐
  Browser/App ───►  │  mitmproxy   │ ──► AI Service (OpenAI, Anthropic, Google)
                    │  + addon     │
                    └──────┬───────┘
                           │ POST /api/events
                    ┌──────▼───────┐         ┌─────────────┐
                    │   FastAPI    │ ──────►  │   Twilio    │ ──► Phone Call
                    │   Backend    │ ◄──────  │   Media     │
                    └──────┬───────┘         │   Streams   │
                           │                  └─────────────┘
                           │ WebSocket                │
                    ┌──────▼───────┐         ┌────────▼──────┐
                    │    React     │         │   Deepgram    │
                    │  Dashboard   │         │  Voice Agent  │
                    └──────────────┘         └───────────────┘
```

### Call Flow

1. Proxy detects high-risk PHI event (severity critical/high, risk score >= 70)
2. Backend triggers outbound call via Twilio REST API
3. Twilio fetches TwiML from `/api/twiml/{call_db_id}` — plays greeting, opens Media Stream
4. Twilio connects bidirectional WebSocket to `/api/voice-agent/{call_db_id}`
5. Bridge relays mulaw audio between Twilio Media Streams and Deepgram Voice Agent API
6. Compliance officer talks to the AI agent about the PHI event
7. Officer can say "mark as mitigated" or "mark as resolved" — agent updates the event via function calling

| Component | Stack | Port |
|-----------|-------|------|
| Proxy | mitmproxy + Python addon (Presidio NLP) | 8080 |
| Backend | FastAPI, PostgreSQL 14, psycopg2 | 8000 |
| Dashboard | React 18, Vite, D3.js, TailwindCSS | 3000 |
| Voice Alerts | Twilio + Deepgram Voice Agent + GPT-4o-mini | - |

---

## Quick Start

### One-command setup (macOS)

```bash
bash setup.sh
```

This will:
- Install prerequisites (mitmproxy, cloudflared)
- Trust the mitmproxy CA certificate
- Build and start Docker containers
- Seed the database with demo events
- Start the mitmproxy interception proxy
- Launch a proxied Chrome window with the dashboard

### Manual setup

#### 1. Start the backend + dashboard + database

```bash
docker compose up --build
```

#### 2. Seed demo data

```bash
curl -X POST http://localhost:8000/api/seed
```

#### 3. Open the dashboard

Navigate to [http://localhost:3000](http://localhost:3000)

#### 4. Start the proxy (separate terminal)

```bash
mitmdump -s shadowguard_addon.py --listen-port 8080 --set block_global=false --set stream_large_bodies=1m
```

#### 5. Launch a proxied Chrome

```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --proxy-server='http://localhost:8080' \
  --user-data-dir=/tmp/mediproxy-chrome \
  --no-first-run \
  "http://localhost:3000"
```

---

## Twilio Voice Alerts + Deepgram Voice Agent

When a high-risk PHI exposure is detected, MediProxy automatically calls the compliance officer via Twilio. The call connects to a Deepgram-powered AI voice agent that:

- Briefs the officer on the PHI event (service, PHI types, risk score, severity, patient name if detected)
- Answers questions about the event details
- Can mark the event as "mitigated" or "resolved" via voice commands (with confirmation)
- Updates the dashboard in real-time via WebSocket broadcast

### Twilio Setup

1. Sign up at [console.twilio.com](https://console.twilio.com)
2. Get your Account SID and Auth Token from the dashboard
3. Buy a phone number with Voice capability
4. If on a trial account, verify the phone number you want to call under Phone Numbers → Verified Caller IDs

### Deepgram Setup

1. Sign up at [deepgram.com](https://deepgram.com)
2. Create an API key from the console

### Tunnel Setup (for local development)

Twilio needs to reach your local backend. Use cloudflared:

```bash
cloudflared tunnel --url http://localhost:8000
```

Copy the generated URL hostname (e.g., `something.trycloudflare.com`) into your `.env` as `SERVICE_HOST`.

### Configuration

Add to `.env`:

```env
TELEPHONY_ENABLED=true
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+1XXXXXXXXXX
ALERT_PHONE_NUMBER=+1XXXXXXXXXX
CALL_COOLDOWN_SECONDS=300
DEEPGRAM_API_KEY=your_deepgram_api_key
SERVICE_HOST=your-tunnel-hostname.trycloudflare.com
```

### Test a call

```bash
curl -X POST http://localhost:8000/api/calls/test
```

You'll hear:
1. Twilio trial disclaimer (press any key)
2. "Please hold, connecting you to the MediProxy compliance agent."
3. The Deepgram voice agent briefs you on the PHI event
4. Say "mark as mitigated" or "resolve this event" to update status

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes (Docker sets it) | `postgresql://shadowguard:shadowguard@localhost:5432/shadowguard` | PostgreSQL connection string |
| `TELEPHONY_ENABLED` | No | `false` | Enable Twilio voice call alerts |
| `TWILIO_ACCOUNT_SID` | For calls | - | Twilio account SID |
| `TWILIO_AUTH_TOKEN` | For calls | - | Twilio auth token |
| `TWILIO_PHONE_NUMBER` | For calls | - | Your Twilio phone number (caller ID) |
| `ALERT_PHONE_NUMBER` | For calls | - | Phone number to receive alert calls |
| `CALL_COOLDOWN_SECONDS` | No | `300` | Minimum seconds between calls per source IP |
| `DEEPGRAM_API_KEY` | For voice agent | - | Deepgram API key for the voice agent |
| `SERVICE_HOST` | For calls | `localhost` | Hostname for Twilio TwiML/WebSocket URLs (set to your tunnel URL) |

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Health check |
| `POST` | `/api/events` | Ingest event from mitmproxy |
| `GET` | `/api/events` | List events (supports `limit`, `offset`, `severity`, `service`, `status`) |
| `GET` | `/api/events/:id` | Get single event |
| `PATCH` | `/api/events/:id/status` | Update event status (active/mitigated/resolved) |
| `GET` | `/api/stats` | Dashboard aggregate statistics |
| `POST` | `/api/seed` | Seed database with demo data |
| `GET` | `/api/calls` | List call records |
| `GET` | `/api/calls/stats` | Voice call aggregate stats |
| `POST` | `/api/calls/test` | Trigger a test call |
| `GET/POST` | `/api/twiml/:id` | TwiML endpoint for Twilio (returns XML with `<Say>` + `<Connect><Stream>`) |
| `WS` | `/api/voice-agent/:id` | WebSocket bridge: Twilio Media Streams ↔ Deepgram Voice Agent |
| `WS` | `/api/ws` | WebSocket for real-time dashboard updates |

---

## Testing Interception

### Browser test (recommended)

1. Run `bash setup.sh` or start the proxy manually
2. In the proxied Chrome, go to [chatgpt.com](https://chatgpt.com)
3. Type a message containing PHI: "Summarize notes for patient John Doe, SSN 423-91-8847, DOB 03/15/1958"
4. Watch the dashboard update in real-time
5. If the event is high-risk, your phone rings with the voice agent

### Terminal test

```bash
export HTTPS_PROXY=http://localhost:8080
export SSL_CERT_FILE=~/.mitmproxy/mitmproxy-ca-cert.pem

# PHI request — detected and redacted
curl -X POST https://api.openai.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-fake-test-key" \
  -d '{"model": "gpt-4", "messages": [{"role": "user", "content": "Patient John Doe, SSN: 423-91-8847, DOB: 03/15/1958. Diagnosis E11.9 Type 2 Diabetes."}]}'
```

---

## Project Structure

```
MediProxy-AI/
├── shadowguard_addon.py    # mitmproxy addon — intercepts, detects PHI, posts to backend
├── phi_redactor.py         # PHI detection engine (Presidio + regex fallback)
├── setup.sh                # One-command setup script
├── docker-compose.yml      # PostgreSQL + backend + dashboard
├── .env                    # Twilio, Deepgram, and other config
├── backend/
│   ├── main.py             # FastAPI app, TwiML endpoint, voice agent bridge, routes
│   ├── database.py         # PostgreSQL connection pool, table creation
│   ├── models.py           # Pydantic request/response models
│   ├── seed.py             # Demo data generator
│   ├── vapi_caller.py      # Twilio call creation, cooldown logic
│   ├── deepgram_agent.py   # Deepgram Voice Agent config, WebSocket connection
│   ├── requirements.txt    # Python dependencies
│   ├── Dockerfile
│   └── tests/
│       ├── test_voice_agent_unit.py              # Unit tests
│       └── test_twilio_migration_properties.py   # Property-based tests (Hypothesis)
└── dashboard/
    ├── src/
    │   ├── App.jsx
    │   ├── components/     # StatsCards, ThreatFeed, TrafficTimeline, RiskHeatmap, etc.
    │   ├── hooks/          # useWebSocket with auto-reconnect
    │   └── lib/            # REST API client
    ├── package.json
    └── Dockerfile
```

---

## Troubleshooting

**"SSL certificate verify failed" in proxied Chrome**
Trust the mitmproxy CA cert: `sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain ~/.mitmproxy/mitmproxy-ca-cert.pem`
Or visit `http://mitm.it` in the proxied browser and install the cert.

**Twilio call says "press any key" then "we are sorry, goodbye"**
Twilio can't reach your TwiML endpoint. Make sure cloudflared is running, `SERVICE_HOST` in `.env` matches the tunnel URL, and you restarted the backend after changing it.

**Twilio call connects but voice agent is silent**
Check `docker compose logs backend` for Deepgram errors. Common causes: invalid `DEEPGRAM_API_KEY`, or the Deepgram WebSocket connection failed.

**"No event found for call_db_id"**
The test call endpoint creates a real event now. If you see this, seed the database first: `curl -X POST http://localhost:8000/api/seed`

**Dashboard not updating**
Check the WebSocket connection indicator in the header. The dashboard auto-reconnects if the connection drops.

**Proxy browser is slow**
mitmproxy decrypts all HTTPS traffic. The addon only scans AI service domains, but TLS interception adds overhead to every connection.
