# ShadowGuard - Test Results

## Setup Summary

✅ All components successfully installed and running:

### Docker Services (Port Mapping)
- PostgreSQL: Port 5433 (mapped from 5432 to avoid conflicts)
- Backend API: Port 8000
- Dashboard: Port 3000

### Proxy
- mitmproxy: Port 8080
- CA Certificate: `~/.mitmproxy/mitmproxy-ca-cert.pem`
- PHI Engine: regex_fallback (Presidio not installed, but working)

## Test Results

### Test 1: PHI Detection ✅
**Request:** Patient data with SSN, DOB, and diagnosis code
```
"Summarize notes for patient John Doe, SSN: 423-91-8847, DOB: 03/15/1958. Diagnosis E11.9 Type 2 Diabetes."
```

**Results:**
- Risk Score: 100/100 (Critical)
- PHI Detected: 3 entities
  - SSN: 423-91-8847
  - DOB: 03/15/1958
  - Patient Name: John Doe
- Action: Redacted and forwarded
- Backend logged: ✅ Event ID 76

### Test 2: Clean Request ✅
**Request:** General programming question
```
"How do I sort a list in Python?"
```

**Results:**
- Risk Score: 20/100 (Low)
- PHI Detected: None
- Action: Passed through cleanly
- Backend logged: ✅

### Test 3: Dashboard Stats ✅
- Total Requests: 77 (75 seeded + 2 live tests)
- PHI Detected: 25 events
- Requests Redacted: 25
- Clean Requests: 52
- Average Risk Score: 39.1

## Access URLs

- Dashboard: http://localhost:3000
- Backend API: http://localhost:8000
- API Health: http://localhost:8000/api/health
- API Docs: http://localhost:8000/docs

## Next Steps

### To test with a browser:
```bash
# Launch Chrome with proxy
open -na "Google Chrome" --args \
  --proxy-server="http://localhost:8080" \
  --user-data-dir="/tmp/chrome-proxy-test"

# Visit http://mitm.it to install the CA certificate
# Then navigate to https://chatgpt.com or https://claude.ai
```

### To test with curl:
```bash
export HTTPS_PROXY=http://localhost:8080
export SSL_CERT_FILE=~/.mitmproxy/mitmproxy-ca-cert.pem

curl -X POST https://api.openai.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-fake-test-key" \
  -d '{"model": "gpt-4", "messages": [{"role": "user", "content": "Your message here"}]}'
```

### To stop the system:
```bash
# Stop the proxy (Ctrl+C in the terminal where it's running)
# Or use: pkill -f mitmdump

# Stop Docker services
docker compose down
```

## Optional: Install Presidio for Better PHI Detection

For production-grade PHI detection using Microsoft Presidio:

```bash
pip3 install presidio-analyzer presidio-anonymizer
python3 -m spacy download en_core_web_lg

# Restart the proxy
mitmdump -s shadowguard_addon.py --listen-port 8080
```

## VAPI Voice Alerts (Optional)

To enable voice call alerts for high-risk events:

1. Sign up at https://vapi.ai
2. Configure a phone number and assistant
3. Update `.env` with your credentials:
   ```
   VAPI_ENABLED=true
   VAPI_API_KEY=your-key
   VAPI_PHONE_NUMBER_ID=your-phone-id
   VAPI_ASSISTANT_ID=your-assistant-id
   ALERT_PHONE_NUMBER=+1XXXXXXXXXX
   ```
4. Restart Docker services: `docker compose down && docker compose up -d`
