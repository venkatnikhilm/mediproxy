"""
Shared test fixtures.

Mocks psycopg2 and twilio at the module level so that importing
backend modules never hits real database or Twilio connections.
"""

import sys
from unittest.mock import MagicMock

# ── Mock psycopg2 before any backend module is imported ────
_mock_psycopg2 = MagicMock()
_mock_psycopg2.pool = MagicMock()
_mock_psycopg2.extras = MagicMock()
sys.modules.setdefault("psycopg2", _mock_psycopg2)
sys.modules.setdefault("psycopg2.pool", _mock_psycopg2.pool)
sys.modules.setdefault("psycopg2.extras", _mock_psycopg2.extras)

# ── Mock twilio ────────────────────────────────────────────
_mock_twilio = MagicMock()
_mock_twilio.rest = MagicMock()
_mock_twilio.rest.Client = MagicMock()
sys.modules.setdefault("twilio", _mock_twilio)
sys.modules.setdefault("twilio.rest", _mock_twilio.rest)
