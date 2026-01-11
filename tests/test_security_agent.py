"""Tests for SecurityAgent."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agents.security_agent.agent import SecurityAgent
from agents.security_agent.model import SecurityConfig, SecurityEvent, SecurityInput


def test_detect_unknown_user_and_auth_fail() -> None:
    agent = SecurityAgent()
    payload = SecurityInput(
        security_event_log=[
            SecurityEvent(
                timestamp="2025-01-01T10:00:00Z",
                agent="Integration",
                event="api_key_access",
                user="unknown",
                ip="203.0.113.99",
                status="failed",
            )
        ],
        config=SecurityConfig(
            sensitive_agents=["Integration"],
            allowlist_users=["operator"],
            allowlist_ip_ranges=["192.168.1.0/24"],
            alert_priority={"api_key_access": "high"},
        ),
    )

    result = agent.run(payload)

    assert result.meta.event_count == 1
    assert result.meta.critical_count == 1
    assert result.security_report[0].priority == "critical"

    flag_codes = {flag.code for flag in result.security_report[0].flag}
    assert "suspicious_access" in flag_codes
    assert "auth_fail" in flag_codes
    assert any(
        action.startswith("Block IP")
        for action in result.security_report[0].suggested_action
    )
    assert "Reset credential" in result.security_report[0].suggested_action
    assert len(result.incident_alert) == 1


def test_recurring_risk_detection() -> None:
    agent = SecurityAgent()
    payload = SecurityInput(
        security_event_log=[
            SecurityEvent(
                timestamp="2025-01-01T10:00:00Z",
                agent="Monitor",
                event="heartbeat",
                user="operator",
                ip="10.1.2.3",
                status="success",
            ),
            SecurityEvent(
                timestamp="2025-01-01T10:05:00Z",
                agent="Monitor",
                event="heartbeat",
                user="operator",
                ip="10.1.2.3",
                status="success",
            ),
        ],
        config=SecurityConfig(
            allowlist_users=["operator"],
            allowlist_ip_ranges=["10.0.0.0/8"],
        ),
    )

    result = agent.run(payload)

    assert result.meta.event_count == 2
    assert len(result.recurring_risk) == 1
    assert result.recurring_risk[0].event_type == "heartbeat"
    assert result.recurring_risk[0].status == "success"
    assert result.recurring_risk[0].count == 2
