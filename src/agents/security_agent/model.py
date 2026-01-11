"""Security Agent models."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SecurityEvent(BaseModel):
    """Raw security event entry."""

    timestamp: str
    agent: str
    event: str
    user: str
    ip: str
    status: str


class SecurityConfig(BaseModel):
    """Security analysis configuration."""

    sensitive_agents: list[str] = Field(default_factory=list)
    monitor_event: list[str] = Field(default_factory=list)
    allowlist_users: list[str] = Field(default_factory=list)
    allowlist_ip_ranges: list[str] = Field(default_factory=list)
    alert_priority: dict[str, str] = Field(default_factory=dict)


class SecurityInput(BaseModel):
    """Input payload for SecurityAgent."""

    security_event_log: list[SecurityEvent]
    config: SecurityConfig


class SecurityFlag(BaseModel):
    """Flag applied to analyzed events."""

    code: str
    message: str


class AnalyzedEvent(SecurityEvent):
    """Event enriched with flags and priority."""

    flag: list[SecurityFlag] = Field(default_factory=list)
    priority: str = "low"
    suggested_action: list[str] = Field(default_factory=list)


class IncidentAlert(BaseModel):
    """Incident alert for high/critical events."""

    timestamp: str
    agent: str
    event: str
    severity: str
    summary: str
    recipient: list[str]
    suggested_action: list[str]


class RecurringRisk(BaseModel):
    """Recurring risk summary."""

    event_type: str
    status: str
    count: int
    time_window_hours: int
    message: str


class SecurityReportMeta(BaseModel):
    """Metadata for security report."""

    event_count: int
    critical_count: int
    high_count: int
    medium_count: int
    self_check: dict[str, bool]


class SecurityOutput(BaseModel):
    """Security report output."""

    security_report: list[AnalyzedEvent]
    incident_alert: list[IncidentAlert]
    recurring_risk: list[RecurringRisk]
    meta: SecurityReportMeta
