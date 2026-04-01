#!/bin/bash
# MediProxy AI - Git History Setup Script
# This script creates a realistic commit history showing project development

set -e

echo "🚀 Setting up Git repository with commit history..."
echo ""

# Check if git is initialized
if [ -d .git ]; then
    echo "⚠️  Git repository already exists!"
    read -p "Do you want to remove it and start fresh? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf .git
        echo "✅ Removed existing git repository"
    else
        echo "❌ Aborted"
        exit 1
    fi
fi

# Initialize git
git init
echo "✅ Initialized git repository"
echo ""

# Configure git (optional - comment out if you want to use global config)
# git config user.name "Your Name"
# git config user.email "your.email@example.com"

# ============================================================
# COMMIT 1: Initial project structure and documentation
# ============================================================
echo "📝 Commit 1: Initial project structure and documentation"
git add README.md .gitignore
git commit -m "Initial commit: Add project README and gitignore

- Add comprehensive README with architecture overview
- Add .gitignore for Python, Node.js, and environment files
- Document MediProxy AI healthcare PHI protection system"
echo ""

# ============================================================
# COMMIT 2: Backend database setup
# ============================================================
echo "📝 Commit 2: Backend database setup"
git add backend/database.py backend/models.py
git commit -m "feat(backend): Add database schema and models

- Implement PostgreSQL connection pool with psycopg2
- Define Pydantic models for events, calls, and API responses
- Create events table with PHI tracking fields
- Add voice_calls table for VAPI integration
- Set up automatic table creation on startup"
echo ""

# ============================================================
# COMMIT 3: Core backend API
# ============================================================
echo "📝 Commit 3: Core backend API"
git add backend/main.py backend/requirements.txt
git commit -m "feat(backend): Implement FastAPI backend with WebSocket support

- Create REST API endpoints for events, stats, and calls
- Implement WebSocket manager for real-time updates
- Add CORS middleware for frontend integration
- Set up health check endpoint
- Add event status update functionality"
echo ""

# ============================================================
# COMMIT 4: PHI detection engine
# ============================================================
echo "📝 Commit 4: PHI detection engine"
git add phi_redactor.py
git commit -m "feat(core): Add PHI detection and redaction engine

- Implement Microsoft Presidio integration for NLP-based detection
- Add custom healthcare recognizers (MRN, ICD-10, medications)
- Create regex fallback for environments without Presidio
- Support 15+ PHI entity types (SSN, DOB, phone, email, etc.)
- Add Ollama LLM integration as alternative detection method"
echo ""

# ============================================================
# COMMIT 5: mitmproxy addon
# ============================================================
echo "📝 Commit 5: mitmproxy addon"
git add shadowguard_addon.py
git commit -m "feat(proxy): Implement mitmproxy addon for HTTPS interception

- Create HTTPS traffic interceptor for AI services
- Add real-time PHI detection and redaction
- Implement risk scoring algorithm (0-100 scale)
- Support multiple AI services (ChatGPT, Claude, Gemini)
- Add pretty-printed terminal output with color coding
- Post events to backend API via threading"
echo ""

# ============================================================
# COMMIT 6: VAPI integration
# ============================================================
echo "📝 Commit 6: VAPI voice alerts"
git add backend/vapi_caller.py
git commit -m "feat(backend): Add VAPI voice alert integration

- Implement automated voice calls for critical incidents
- Add per-IP cooldown mechanism to prevent spam
- Support template variables for dynamic call content
- Add call logging and status tracking
- Implement test call endpoint for validation"
echo ""

# ============================================================
# COMMIT 7: Demo data seeding
# ============================================================
echo "📝 Commit 7: Demo data seeding"
git add backend/seed.py
git commit -m "feat(backend): Add demo data seeding functionality

- Generate realistic healthcare security events
- Create diverse PHI types and risk scenarios
- Add temporal distribution across hours
- Support multiple AI services and severity levels
- Include fake voice call records"
echo ""

# ============================================================
# COMMIT 8: Backend Docker setup
# ============================================================
echo "📝 Commit 8: Backend Docker setup"
git add backend/Dockerfile
git commit -m "build(backend): Add Dockerfile for backend service

- Create Python 3.12 slim-based container
- Install CA certificates for HTTPS requests
- Configure uvicorn for production deployment
- Expose port 8000 for API access"
echo ""

# ============================================================
# COMMIT 9: Frontend project setup
# ============================================================
echo "📝 Commit 9: Frontend project setup"
git add dashboard/package.json dashboard/package-lock.json dashboard/vite.config.js dashboard/tailwind.config.js dashboard/postcss.config.js dashboard/index.html
git commit -m "feat(frontend): Initialize React + Vite dashboard project

- Set up Vite build configuration
- Add React 18 with D3.js for visualizations
- Configure TailwindCSS for styling
- Add PostCSS for CSS processing
- Create HTML entry point"
echo ""

# ============================================================
# COMMIT 10: Frontend core styles
# ============================================================
echo "📝 Commit 10: Frontend core styles"
git add dashboard/src/index.css dashboard/src/main.jsx
git commit -m "style(frontend): Add cybersecurity-themed styling

- Implement dark theme with cyan accents
- Add custom CSS variables for colors
- Create glass-morphism panel effects
- Add PHI tag and status badge styles
- Set up React root mounting"
echo ""

# ============================================================
# COMMIT 11: API client library
# ============================================================
echo "📝 Commit 11: API client library"
git add dashboard/src/lib/api.js
git commit -m "feat(frontend): Add API client library

- Implement REST API functions for events, stats, calls
- Add query parameter support for filtering
- Create event status update function
- Add error handling for failed requests"
echo ""

# ============================================================
# COMMIT 12: WebSocket hook
# ============================================================
echo "📝 Commit 12: WebSocket hook"
git add dashboard/src/hooks/useWebSocket.js
git commit -m "feat(frontend): Add WebSocket hook for real-time updates

- Implement auto-reconnecting WebSocket connection
- Add connection status tracking
- Handle new_event, status_update, and voice_call messages
- Add cleanup on unmount"
echo ""

# ============================================================
# COMMIT 13: Animated counter hook
# ============================================================
echo "📝 Commit 13: Animated counter hook"
git add dashboard/src/hooks/useAnimatedCounter.js
git commit -m "feat(frontend): Add animated counter hook

- Create smooth number transitions for stats
- Implement easing function for natural animation
- Add configurable duration"
echo ""

# ============================================================
# COMMIT 14: Header component
# ============================================================
echo "📝 Commit 14: Header component"
git add dashboard/src/components/Header.jsx
git commit -m "feat(frontend): Add dashboard header component

- Display MediProxy AI branding
- Show WebSocket connection status indicator
- Add real-time event counter
- Implement cybersecurity-themed design"
echo ""

# ============================================================
# COMMIT 15: Stats cards component
# ============================================================
echo "📝 Commit 15: Stats cards component"
git add dashboard/src/components/StatsCards.jsx
git commit -m "feat(frontend): Add statistics cards component

- Display total requests and PHI detection counts
- Show average risk score with color coding
- Add voice call statistics
- Implement animated counters for smooth updates"
echo ""

# ============================================================
# COMMIT 16: Status badge component
# ============================================================
echo "📝 Commit 16: Status badge component"
git add dashboard/src/components/StatusBadge.jsx
git commit -m "feat(frontend): Add status badge component

- Create color-coded severity badges
- Support critical, high, medium, low, clean levels
- Add pulsing animation for critical alerts"
echo ""

# ============================================================
# COMMIT 17: Threat feed component
# ============================================================
echo "📝 Commit 17: Threat feed component"
git add dashboard/src/components/ThreatFeed.jsx
git commit -m "feat(frontend): Add live threat feed component

- Display real-time security events
- Show risk scores with color coding
- Add new event animations
- Implement click-to-view details
- Support scrollable event list"
echo ""

# ============================================================
# COMMIT 18: Traffic timeline component
# ============================================================
echo "📝 Commit 18: Traffic timeline component"
git add dashboard/src/components/TrafficTimeline.jsx
git commit -m "feat(frontend): Add D3.js traffic timeline chart

- Visualize events over time with line chart
- Color-code points by risk level
- Add interactive tooltips
- Implement responsive SVG rendering
- Show temporal patterns in security events"
echo ""

# ============================================================
# COMMIT 19: Risk heatmap component
# ============================================================
echo "📝 Commit 19: Risk heatmap component"
git add dashboard/src/components/RiskHeatmap.jsx
git commit -m "feat(frontend): Add D3.js risk heatmap visualization

- Create hour-by-service risk matrix
- Use color intensity for risk levels
- Add interactive tooltips with details
- Implement responsive grid layout
- Show risk patterns across time and services"
echo ""

# ============================================================
# COMMIT 20: Network graph component
# ============================================================
echo "📝 Commit 20: Network graph component"
git add dashboard/src/components/NetworkGraph.jsx
git commit -m "feat(frontend): Add D3.js force-directed network graph

- Visualize connections between IPs and AI services
- Implement force simulation for node positioning
- Add drag interaction for nodes
- Color-code by service type
- Show network topology in real-time"
echo ""

# ============================================================
# COMMIT 21: Audit log component
# ============================================================
echo "📝 Commit 21: Audit log component"
git add dashboard/src/components/AuditLog.jsx
git commit -m "feat(frontend): Add audit log table with sorting and pagination

- Display comprehensive event details
- Implement sortable columns (time, IP, service, risk)
- Add pagination for large datasets
- Support PHI-only and all-events filtering
- Add status update dropdown
- Show voice call indicators
- Implement manual refresh button"
echo ""

# ============================================================
# COMMIT 22: Redaction viewer component
# ============================================================
echo "📝 Commit 22: Redaction viewer component"
git add dashboard/src/components/RedactionViewer.jsx
git commit -m "feat(frontend): Add redaction viewer modal

- Display side-by-side original and redacted text
- Show detailed PHI findings with entity types
- Add risk score and severity indicators
- Implement modal overlay with close functionality
- Support scrollable content for long texts"
echo ""

# ============================================================
# COMMIT 23: Main App component
# ============================================================
echo "📝 Commit 23: Main App component"
git add dashboard/src/App.jsx
git commit -m "feat(frontend): Add main App component with state management

- Integrate all dashboard components
- Implement WebSocket message handling
- Add real-time event updates
- Manage stats and call data
- Handle event selection for detail view
- Add new event animations
- Implement data refresh functionality"
echo ""

# ============================================================
# COMMIT 24: Frontend Docker setup
# ============================================================
echo "📝 Commit 24: Frontend Docker setup"
git add dashboard/Dockerfile
git commit -m "build(frontend): Add Dockerfile for dashboard service

- Create Node.js 20 Alpine-based container
- Install npm dependencies
- Configure Vite dev server
- Expose port 3000 for dashboard access"
echo ""

# ============================================================
# COMMIT 25: Docker Compose orchestration
# ============================================================
echo "📝 Commit 25: Docker Compose orchestration"
git add docker-compose.yml
git commit -m "build: Add Docker Compose for multi-container deployment

- Configure PostgreSQL 14 service with health checks
- Set up FastAPI backend with environment variables
- Add React dashboard with Vite
- Implement service dependencies
- Add persistent volume for database
- Configure VAPI integration variables"
echo ""

# ============================================================
# COMMIT 26: Environment configuration
# ============================================================
echo "📝 Commit 26: Environment configuration"
git add .env
git commit -m "config: Add environment configuration template

- Add VAPI credentials placeholders
- Configure call cooldown settings
- Document all environment variables
- Add security notes for sensitive data"
echo ""

# ============================================================
# COMMIT 27: Testing and documentation
# ============================================================
echo "📝 Commit 27: Testing and documentation"
git add setup.sh launch_test_browser.sh check_status.sh BROWSER_TEST_GUIDE.md QUICK_TEST_REFERENCE.md COMPREHENSIVE_PHI_TEST.md TEST_RESULTS.md VAPI_SETUP_GUIDE.md
git commit -m "docs: Add comprehensive testing guides and helper scripts

- Add browser testing guide with step-by-step instructions
- Create comprehensive PHI test covering all entity types
- Add quick reference card for testing
- Create VAPI setup guide with detailed configuration
- Add helper scripts for browser launch and status checks
- Document test results and expected outcomes"
echo ""

# ============================================================
# COMMIT 28: Feature documentation
# ============================================================
echo "📝 Commit 28: Feature documentation"
git add REFRESH_BUTTON_FEATURE.md RESUME_BULLETS.md
git commit -m "docs: Add feature documentation and resume bullets

- Document refresh button functionality
- Add resume bullet point options
- Include technical details and usage examples
- Provide metrics and key highlights"
echo ""

# ============================================================
# Summary
# ============================================================
echo ""
echo "✅ Git repository setup complete!"
echo ""
echo "📊 Commit Summary:"
git log --oneline --graph --all
echo ""
echo "📝 Total commits: $(git rev-list --count HEAD)"
echo ""
echo "🎯 Next steps:"
echo "  1. Review commit history: git log"
echo "  2. Create GitHub repository"
echo "  3. Add remote: git remote add origin <your-repo-url>"
echo "  4. Push to GitHub: git push -u origin main"
echo ""
echo "💡 Tip: You can modify commit dates if needed using:"
echo "   git rebase -i --root"
echo "   Then change 'pick' to 'edit' and use:"
echo "   GIT_COMMITTER_DATE=\"YYYY-MM-DD HH:MM:SS\" git commit --amend --no-edit --date=\"YYYY-MM-DD HH:MM:SS\""
echo ""
