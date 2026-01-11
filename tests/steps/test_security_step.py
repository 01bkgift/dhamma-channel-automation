"""
Tests for Security pipeline step.
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from steps.security import SecurityStep


class TestSecurityStep:
    """Test SecurityStep integration."""

    @pytest.fixture
    def step(self):
        return SecurityStep()

    @pytest.fixture
    def context(self, tmp_path):
        return {
            "events": [
                {
                    "timestamp": "2025-01-01T10:00:00Z",
                    "agent": "Integration",
                    "event": "api_key_access",
                    "user": "unknown",
                    "ip": "203.0.113.99",
                    "status": "failed",
                }
            ],
            "config": {
                "sensitive_agents": ["Integration"],
                "allowlist_users": ["operator"],
                "allowlist_ip_ranges": ["192.168.1.0/24"],
                "alert_priority": {"api_key_access": "high"},
            },
            "output_dir": str(tmp_path),
        }

    def test_step_execute(self, step, context):
        result = step.execute(context)

        assert result["status"] == "success"
        assert Path(result["output_file"]).exists()
        assert Path(result["report_file"]).exists()
        assert result["event_count"] == 1
        assert result["incident_count"] == 1

    def test_step_output_schema(self, step, context):
        result = step.execute(context)

        with open(result["output_file"], encoding="utf-8") as f:
            data = json.load(f)

        assert "security_report" in data
        assert "incident_alert" in data
        assert "recurring_risk" in data
        assert "meta" in data
        assert data["meta"]["event_count"] == 1
