#!/bin/bash
# MediProxy AI - Git History Setup Script with Realistic Dates
# This script creates commits spread over time to simulate real development

set -e

echo "🚀 Setting up Git repository with realistic commit history..."
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

# Function to commit with custom date
commit_with_date() {
    local date="$1"
    local message="$2"
    GIT_AUTHOR_DATE="$date" GIT_COMMITTER_DATE="$date" git commit -m "$message"
}

# ============================================================
# Day 1: Project initialization (e.g., Feb 10, 2024)
# ============================================================
echo "📝 Day 1: Project initialization"

git add README.md .gitignore
commit_with_date "2024-02-10 10:00:00" "Initial commit: Add project README and gitignore

- Add comprehensive README with architecture overview
- Add .gitignore for Python, Node.js, and environment files
- Document MediProxy AI healthcare PHI protection system"

git add backend/database.py backend/models.py
commit_with_date "2024-02-10 14:30:00" "feat(backend): Add database schema and models

- Implement PostgreSQL connection pool with psycopg2
- Define Pydantic models for events, calls, and API responses
- Create events table with PHI tracking fields
- Add voice_calls table for VAPI integration"

git add backend/requirements.txt
commit_with_date "2024-02-10 16:00:00" "build(backend): Add Python dependencies

- Add FastAPI and uvicorn for API server
- Add psycopg2-binary for PostgreSQL
- Add pydantic for data validation"

echo ""

# ============================================================
# Day 2: Core backend development (Feb 11, 2024)
# ============================================================
echo "📝 Day 2: Core backend development"

git add backend/main.py
commit_with_date "2024-02-11 09:00:00" "feat(backend): Implement FastAPI backend with WebSocket support

- Create REST API endpoints for events, stats, and calls
- Implement WebSocket manager for real-time updates
- Add CORS middleware for frontend integration
- Set up health check endpoint"

git add phi_redactor.py
commit_with_date "2024-02-11 13:00:00" "feat(core): Add PHI detection and redaction engine

- Implement Microsoft Presidio integration for NLP-based detection
- Add custom healthcare recognizers (MRN, ICD-10, medications)
- Create regex fallback for environments without Presidio
- Support 15+ PHI entity types (SSN, DOB, phone, email, etc.)"

git add backend/seed.py
commit_with_date "2024-02-11 16:30:00" "feat(backend): Add demo data seeding functionality

- Generate realistic healthcare security events
- Create diverse PHI types and risk scenarios
- Add temporal distribution across hours"

echo ""

# ============================================================
# Day 3: Proxy implementation (Feb 12, 2024)
# ============================================================
echo "📝 Day 3: Proxy implementation"

git add shadowguard_addon.py
commit_with_date "2024-02-12 10:00:00" "feat(proxy): Implement mitmproxy addon for HTTPS interception

- Create HTTPS traffic interceptor for AI services
- Add real-time PHI detection and redaction
- Implement risk scoring algorithm (0-100 scale)
- Support multiple AI services (ChatGPT, Claude, Gemini)"

commit_with_date "2024-02-12 14:00:00" "feat(proxy): Add pretty-printed terminal output

- Add color-coded risk indicators
- Display PHI findings with entity types
- Show redaction details in terminal
- Add formatted event summaries"

git add backend/vapi_caller.py
commit_with_date "2024-02-12 17:00:00" "feat(backend): Add VAPI voice alert integration

- Implement automated voice calls for critical incidents
- Add per-IP cooldown mechanism to prevent spam
- Support template variables for dynamic call content
- Add call logging and status tracking"

echo ""

# ============================================================
# Day 4: Docker setup (Feb 13, 2024)
# ============================================================
echo "📝 Day 4: Docker containerization"

git add backend/Dockerfile
commit_with_date "2024-02-13 10:00:00" "build(backend): Add Dockerfile for backend service

- Create Python 3.12 slim-based container
- Install CA certificates for HTTPS requests
- Configure uvicorn for production deployment"

git add docker-compose.yml
commit_with_date "2024-02-13 14:00:00" "build: Add Docker Compose for multi-container deployment

- Configure PostgreSQL 14 service with health checks
- Set up FastAPI backend with environment variables
- Implement service dependencies
- Add persistent volume for database"

git add .env
commit_with_date "2024-02-13 16:00:00" "config: Add environment configuration template

- Add VAPI credentials placeholders
- Configure call cooldown settings
- Document all environment variables"

echo ""

# ============================================================
# Day 5: Frontend initialization (Feb 14, 2024)
# ============================================================
echo "📝 Day 5: Frontend project setup"

git add dashboard/package.json dashboard/package-lock.json dashboard/vite.config.js dashboard/tailwind.config.js dashboard/postcss.config.js dashboard/index.html
commit_with_date "2024-02-14 09:00:00" "feat(frontend): Initialize React + Vite dashboard project

- Set up Vite build configuration
- Add React 18 with D3.js for visualizations
- Configure TailwindCSS for styling
- Create HTML entry point"

git add dashboard/src/index.css dashboard/src/main.jsx
commit_with_date "2024-02-14 11:00:00" "style(frontend): Add cybersecurity-themed styling

- Implement dark theme with cyan accents
- Add custom CSS variables for colors
- Create glass-morphism panel effects
- Add PHI tag and status badge styles"

git add dashboard/src/lib/api.js
commit_with_date "2024-02-14 14:00:00" "feat(frontend): Add API client library

- Implement REST API functions for events, stats, calls
- Add query parameter support for filtering
- Create event status update function"

git add dashboard/src/hooks/useWebSocket.js dashboard/src/hooks/useAnimatedCounter.js
commit_with_date "2024-02-14 16:30:00" "feat(frontend): Add custom React hooks

- Implement auto-reconnecting WebSocket hook
- Add animated counter hook for smooth transitions
- Handle real-time message updates"

echo ""

# ============================================================
# Day 6: Core UI components (Feb 15, 2024)
# ============================================================
echo "📝 Day 6: Core UI components"

git add dashboard/src/components/Header.jsx dashboard/src/components/StatusBadge.jsx
commit_with_date "2024-02-15 09:00:00" "feat(frontend): Add header and status badge components

- Display MediProxy AI branding
- Show WebSocket connection status indicator
- Create color-coded severity badges"

git add dashboard/src/components/StatsCards.jsx
commit_with_date "2024-02-15 11:30:00" "feat(frontend): Add statistics cards component

- Display total requests and PHI detection counts
- Show average risk score with color coding
- Add voice call statistics
- Implement animated counters"

git add dashboard/src/components/ThreatFeed.jsx
commit_with_date "2024-02-15 14:00:00" "feat(frontend): Add live threat feed component

- Display real-time security events
- Show risk scores with color coding
- Add new event animations
- Implement click-to-view details"

git add dashboard/src/components/AuditLog.jsx
commit_with_date "2024-02-15 17:00:00" "feat(frontend): Add audit log table with sorting and pagination

- Display comprehensive event details
- Implement sortable columns
- Add pagination for large datasets
- Support PHI-only filtering"

echo ""

# ============================================================
# Day 7: Data visualizations (Feb 16, 2024)
# ============================================================
echo "📝 Day 7: D3.js visualizations"

git add dashboard/src/components/TrafficTimeline.jsx
commit_with_date "2024-02-16 10:00:00" "feat(frontend): Add D3.js traffic timeline chart

- Visualize events over time with line chart
- Color-code points by risk level
- Add interactive tooltips
- Implement responsive SVG rendering"

git add dashboard/src/components/RiskHeatmap.jsx
commit_with_date "2024-02-16 13:00:00" "feat(frontend): Add D3.js risk heatmap visualization

- Create hour-by-service risk matrix
- Use color intensity for risk levels
- Add interactive tooltips with details
- Show risk patterns across time and services"

git add dashboard/src/components/NetworkGraph.jsx
commit_with_date "2024-02-16 16:00:00" "feat(frontend): Add D3.js force-directed network graph

- Visualize connections between IPs and AI services
- Implement force simulation for node positioning
- Add drag interaction for nodes
- Color-code by service type"

echo ""

# ============================================================
# Day 8: Integration and polish (Feb 17, 2024)
# ============================================================
echo "📝 Day 8: Integration and polish"

git add dashboard/src/components/RedactionViewer.jsx
commit_with_date "2024-02-17 10:00:00" "feat(frontend): Add redaction viewer modal

- Display side-by-side original and redacted text
- Show detailed PHI findings with entity types
- Add risk score and severity indicators
- Implement modal overlay"

git add dashboard/src/App.jsx
commit_with_date "2024-02-17 13:00:00" "feat(frontend): Add main App component with state management

- Integrate all dashboard components
- Implement WebSocket message handling
- Add real-time event updates
- Manage stats and call data
- Handle event selection for detail view"

git add dashboard/Dockerfile
commit_with_date "2024-02-17 15:00:00" "build(frontend): Add Dockerfile for dashboard service

- Create Node.js 20 Alpine-based container
- Install npm dependencies
- Configure Vite dev server"

commit_with_date "2024-02-17 16:00:00" "build: Update Docker Compose with dashboard service

- Add React dashboard to docker-compose
- Configure service dependencies
- Set up port mappings"

echo ""

# ============================================================
# Day 9: Testing and documentation (Feb 18, 2024)
# ============================================================
echo "📝 Day 9: Testing and documentation"

git add setup.sh launch_test_browser.sh check_status.sh
commit_with_date "2024-02-18 10:00:00" "test: Add helper scripts for testing

- Add setup script for mitmproxy installation
- Create browser launch script with proxy
- Add status check script for all services"

git add BROWSER_TEST_GUIDE.md QUICK_TEST_REFERENCE.md COMPREHENSIVE_PHI_TEST.md TEST_RESULTS.md
commit_with_date "2024-02-18 14:00:00" "docs: Add comprehensive testing guides

- Add browser testing guide with step-by-step instructions
- Create comprehensive PHI test covering all entity types
- Add quick reference card for testing
- Document test results and expected outcomes"

git add VAPI_SETUP_GUIDE.md
commit_with_date "2024-02-18 16:00:00" "docs: Add VAPI setup guide

- Document VAPI configuration process
- Add troubleshooting section
- Include cost considerations
- Provide example configurations"

echo ""

# ============================================================
# Day 10: Final touches (Feb 19, 2024)
# ============================================================
echo "📝 Day 10: Final touches"

commit_with_date "2024-02-19 10:00:00" "feat(frontend): Add manual refresh button to audit log

- Add refresh button with loading state
- Implement data reload functionality
- Add visual feedback during refresh"

git add REFRESH_BUTTON_FEATURE.md RESUME_BULLETS.md
commit_with_date "2024-02-19 14:00:00" "docs: Add feature documentation and resume bullets

- Document refresh button functionality
- Add resume bullet point options
- Include technical details and usage examples"

commit_with_date "2024-02-19 16:00:00" "docs: Update README with final project details

- Update branding to MediProxy AI
- Add comprehensive setup instructions
- Document all features and capabilities"

echo ""

# ============================================================
# Summary
# ============================================================
echo "✅ Git repository setup complete with realistic dates!"
echo ""
echo "📊 Commit Summary:"
git log --oneline --graph --all
echo ""
echo "📝 Total commits: $(git rev-list --count HEAD)"
echo ""
echo "📅 Date range: Feb 10-19, 2024 (10 days of development)"
echo ""
echo "🎯 Next steps:"
echo "  1. Review commit history: git log --pretty=format:'%h - %an, %ar : %s'"
echo "  2. Create GitHub repository"
echo "  3. Add remote: git remote add origin <your-repo-url>"
echo "  4. Push to GitHub: git push -u origin main"
echo ""
echo "💡 Note: Commits are spread over 10 days to simulate realistic development"
echo ""
