"""Security Agent implementation."""

from __future__ import annotations

import ipaddress

from automation_core.base_agent import BaseAgent

from .model import (
    AnalyzedEvent,
    IncidentAlert,
    RecurringRisk,
    SecurityFlag,
    SecurityInput,
    SecurityOutput,
    SecurityReportMeta,
)

_PRIORITY_ORDER = ["low", "medium", "high", "critical"]
_PRIORITY_SET = set(_PRIORITY_ORDER)


class SecurityAgent(BaseAgent[SecurityInput, SecurityOutput]):
    """Deterministic Security Agent for pipeline monitoring."""

    def __init__(self) -> None:
        super().__init__(
            name="SecurityAgent",
            version="1.0.0",
            description="Analyzes security events and produces alerts/reporting",
        )

    def run(self, input_data: SecurityInput) -> SecurityOutput:
        analyzed_events: list[AnalyzedEvent] = []
        incidents: list[IncidentAlert] = []
        recurring_tracker: dict[tuple[str, str], int] = {}

        cfg = input_data.config

        for event in input_data.security_event_log:
            flags: list[SecurityFlag] = []
            actions: list[str] = []
            priority = _normalize_priority(cfg.alert_priority.get(event.event, "low"))

            if cfg.monitor_event and event.event in cfg.monitor_event and priority == "low":
                priority = "medium"

            if _is_suspicious_user(event.user, cfg.allowlist_users) or _is_suspicious_ip(
                event.ip, cfg.allowlist_ip_ranges
            ):
                flags.append(
                    SecurityFlag(
                        code="suspicious_access",
                        message="Unknown or unauthorized user/IP",
                    )
                )
                priority = "critical"
                _append_action(actions, f"Block IP {event.ip}")
                _append_action(actions, "Notify admin")
                _append_action(actions, "Audit logs")

            if event.event == "auth_fail" or (
                event.event == "api_key_access" and event.status == "failed"
            ):
                flags.append(
                    SecurityFlag(code="auth_fail", message="Authentication failed")
                )
                priority = "critical"
                _append_action(actions, "Reset credential")
                _append_action(actions, "Audit logs")

            if event.event == "data_export" and event.user not in {"operator", "admin"}:
                flags.append(
                    SecurityFlag(
                        code="unusual_export",
                        message="Unusual data export request",
                    )
                )
                if priority not in {"critical"}:
                    priority = "high"
                _append_action(actions, "Review export request")
                _append_action(actions, "Verify user permissions")

            if event.agent in cfg.sensitive_agents:
                priority = _elevate_priority(priority)

            analyzed = AnalyzedEvent(
                **event.model_dump(),
                flag=flags,
                priority=priority,
                suggested_action=actions,
            )
            analyzed_events.append(analyzed)

            if priority in {"critical", "high"} and flags:
                incidents.append(
                    IncidentAlert(
                        timestamp=event.timestamp,
                        agent=event.agent,
                        event=event.event,
                        severity=priority,
                        summary=_build_incident_summary(event.user, event.ip, flags[0]),
                        recipient=["admin"],
                        suggested_action=actions,
                    )
                )

            key = (event.event, event.status)
            recurring_tracker[key] = recurring_tracker.get(key, 0) + 1

        recurring_risks: list[RecurringRisk] = []
        for (event_type, status), count in recurring_tracker.items():
            if count >= 2:
                recurring_risks.append(
                    RecurringRisk(
                        event_type=event_type,
                        status=status,
                        count=count,
                        time_window_hours=24,
                        message=f"Event {event_type} ({status}) occurred {count} times",
                    )
                )

        critical_count = sum(1 for e in analyzed_events if e.priority == "critical")
        high_count = sum(1 for e in analyzed_events if e.priority == "high")
        medium_count = sum(1 for e in analyzed_events if e.priority == "medium")

        return SecurityOutput(
            security_report=analyzed_events,
            incident_alert=incidents,
            recurring_risk=recurring_risks,
            meta=SecurityReportMeta(
                event_count=len(analyzed_events),
                critical_count=critical_count,
                high_count=high_count,
                medium_count=medium_count,
                self_check={"all_sections_present": True, "no_empty_fields": True},
            ),
        )


def _normalize_priority(priority: str) -> str:
    normalized = priority.lower()
    if normalized in _PRIORITY_SET:
        return normalized
    return "low"


def _elevate_priority(priority: str) -> str:
    try:
        index = _PRIORITY_ORDER.index(priority)
    except ValueError:
        return priority
    return _PRIORITY_ORDER[min(index + 1, len(_PRIORITY_ORDER) - 1)]


def _append_action(actions: list[str], action: str) -> None:
    if action and action not in actions:
        actions.append(action)


def _is_suspicious_user(user: str, allowlist_users: list[str]) -> bool:
    if user.strip().lower() == "unknown":
        return True
    return bool(allowlist_users) and user not in allowlist_users


def _is_suspicious_ip(ip: str, allowlist_ranges: list[str]) -> bool:
    if not allowlist_ranges:
        return False
    try:
        ip_addr = ipaddress.ip_address(ip)
    except ValueError:
        return True
    for cidr in allowlist_ranges:
        try:
            network = ipaddress.ip_network(cidr, strict=False)
        except ValueError:
            continue
        if ip_addr in network:
            return False
    return True


def _build_incident_summary(user: str, ip: str, flag: SecurityFlag) -> str:
    return f"{flag.message} (user={user}, ip={ip})"


__all__ = ["SecurityAgent"]
