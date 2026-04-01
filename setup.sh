#!/bin/bash
# MediProxy - One-Command Setup
# Starts Docker containers, installs mitmproxy cert, launches proxy + browser
# Usage: bash setup.sh

set -e

PROXY_PORT=8080
CERT_DIR="$HOME/.mitmproxy"
CERT_FILE="$CERT_DIR/mitmproxy-ca-cert.pem"

echo "🛡️  MediProxy Setup"
echo "==================="

# ── Step 1: Check prerequisites ────────────────────────────
echo ""
echo "📋 Checking prerequisites..."

if ! command -v docker &> /dev/null; then
    echo "  ❌ Docker not found. Install Docker Desktop first."
    exit 1
fi
echo "  ✅ Docker"

if ! command -v mitmdump &> /dev/null; then
    echo "  📦 Installing mitmproxy..."
    brew install mitmproxy 2>/dev/null || pip3 install mitmproxy
fi
echo "  ✅ mitmproxy"

if ! command -v cloudflared &> /dev/null; then
    echo "  📦 Installing cloudflared..."
    brew install cloudflared 2>/dev/null || echo "  ⚠️  Install cloudflared manually for Twilio voice calls"
fi
if command -v cloudflared &> /dev/null; then
    echo "  ✅ cloudflared"
fi

# ── Step 2: Generate and trust mitmproxy CA cert ──────────
echo ""
echo "🔐 Setting up mitmproxy CA certificate..."

if [ ! -f "$CERT_FILE" ]; then
    echo "  Generating cert (first-time setup)..."
    timeout 3 mitmdump --listen-port 18080 2>/dev/null || true
    sleep 1
fi

if [ -f "$CERT_FILE" ]; then
    # Check if cert is already trusted
    if security find-certificate -c "mitmproxy" /Library/Keychains/System.keychain &>/dev/null 2>&1 || \
       security find-certificate -c "mitmproxy" ~/Library/Keychains/login.keychain-db &>/dev/null 2>&1; then
        echo "  ✅ CA cert already trusted"
    else
        echo "  Installing CA cert into macOS Keychain (requires password)..."
        sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain "$CERT_FILE" 2>/dev/null && \
            echo "  ✅ CA cert trusted automatically" || {
            echo "  ⚠️  Auto-trust failed. Opening cert manually..."
            open "$CERT_FILE"
            echo "  → Find 'mitmproxy' in Keychain Access"
            echo "  → Double-click → Trust → Always Trust"
            read -p "  Press Enter once you've trusted the cert..."
        }
    fi
else
    echo "  ⚠️  Cert will be generated on first proxy run"
fi

# ── Step 3: Start Docker containers ───────────────────────
echo ""
echo "🐳 Starting Docker containers..."
docker compose down 2>/dev/null || true
docker compose up --build -d

echo "  Waiting for backend to be ready..."
for i in $(seq 1 30); do
    if curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
        echo "  ✅ Backend ready"
        break
    fi
    if [ "$i" -eq 30 ]; then
        echo "  ❌ Backend failed to start. Check: docker compose logs backend"
        exit 1
    fi
    sleep 1
done

echo "  ✅ Dashboard at http://localhost:3000"

# ── Step 4: Seed the database ─────────────────────────────
echo ""
echo "🌱 Seeding database with demo events..."
curl -s -X POST http://localhost:8000/api/seed > /dev/null 2>&1
echo "  ✅ Database seeded"

# ── Step 5: Start mitmproxy in background ─────────────────
echo ""
echo "🔀 Starting mitmproxy..."

# Kill any existing mitmproxy on the port
lsof -ti:$PROXY_PORT | xargs kill -9 2>/dev/null || true
sleep 1

mitmdump -s shadowguard_addon.py --listen-port $PROXY_PORT --set block_global=false --set stream_large_bodies=1m -q &
MITM_PID=$!
sleep 2

if kill -0 $MITM_PID 2>/dev/null; then
    echo "  ✅ mitmproxy running on port $PROXY_PORT (PID: $MITM_PID)"
else
    echo "  ❌ mitmproxy failed to start"
    exit 1
fi

# ── Step 6: Launch proxied Chrome ─────────────────────────
echo ""
echo "🌐 Launching proxied Chrome..."
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
    --proxy-server="http://localhost:$PROXY_PORT" \
    --user-data-dir=/tmp/mediproxy-chrome \
    --no-first-run \
    --no-default-browser-check \
    "http://localhost:3000" &>/dev/null &

echo "  ✅ Proxied Chrome opened with dashboard"

# ── Done ──────────────────────────────────────────────────
echo ""
echo "========================================="
echo "✅ MediProxy is running!"
echo ""
echo "  Dashboard:  http://localhost:3000"
echo "  Backend:    http://localhost:8000"
echo "  Proxy:      localhost:$PROXY_PORT"
echo ""
echo "  Use the proxied Chrome window to browse"
echo "  AI services. PHI will be detected and"
echo "  high-risk events trigger phone calls."
echo ""
echo "  To stop everything:"
echo "    kill $MITM_PID          # stop proxy"
echo "    docker compose down     # stop containers"
echo "========================================="
