"""
Security pipeline step.
Wraps SecurityAgent for orchestrator integration.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import TypedDict

from agents.security_agent.agent import SecurityAgent
from agents.security_agent.model import SecurityConfig, SecurityEvent, SecurityInput
from automation_core.base_step import BaseStep

logger = logging.getLogger(__name__)


class SecurityContext(TypedDict, total=False):
    """Context for SecurityStep."""

    input_log_file: str
    events: list[dict]
    config: dict
    config_file: str
    output_dir: str


class SecurityStep(BaseStep):
    """Pipeline step for security log analysis."""

    def __init__(self) -> None:
        super().__init__(step_id="security", step_type="Security", version="1.0.0")
        self.agent = SecurityAgent()

    def execute(self, context: SecurityContext) -> dict:
        events, config = self._load_payload(context)

        try:
            agent_input = SecurityInput(security_event_log=events, config=config)
        except Exception as exc:
            logger.error("Failed to build SecurityInput: %s", exc)
            return {"status": "error", "error": str(exc)}

        result = self.agent.run(agent_input)

        output_dir = Path(context.get("output_dir", "output"))
        output_dir.mkdir(parents=True, exist_ok=True)

        json_path = output_dir / "security_report.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(result.model_dump(), f, ensure_ascii=False, indent=2, default=str)

        md_path = output_dir / "security_report.md"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(self._render_markdown(result))

        return {
            "status": "success",
            "output_file": str(json_path),
            "report_file": str(md_path),
            "event_count": result.meta.event_count,
            "incident_count": len(result.incident_alert),
        }

    def _load_payload(
        self, context: SecurityContext
    ) -> tuple[list[SecurityEvent], SecurityConfig]:
        events_data: list[dict] | list[SecurityEvent] | None = None
        file_config: SecurityConfig | None = None

        input_log_file = context.get("input_log_file")
        if input_log_file:
            path = Path(input_log_file)
            if path.exists():
                try:
                    payload = json.loads(path.read_text(encoding="utf-8"))
                    if isinstance(payload, dict):
                        events_data = payload.get("security_event_log") or payload.get(
                            "events"
                        )
                        if isinstance(payload.get("config"), dict):
                            try:
                                file_config = SecurityConfig(**payload["config"])
                            except Exception as exc:
                                logger.warning(
                                    "Failed to parse config from input_log_file: %s",
                                    exc,
                                )
                    elif isinstance(payload, list):
                        events_data = payload
                except Exception as exc:
                    logger.warning("Failed to load input_log_file: %s", exc)
            else:
                logger.warning("input_log_file not found: %s", input_log_file)

        if events_data is None:
            events_data = context.get("events", [])

        events: list[SecurityEvent] = []
        for item in events_data:
            if isinstance(item, SecurityEvent):
                events.append(item)
            elif isinstance(item, dict):
                try:
                    events.append(SecurityEvent(**item))
                except Exception as exc:
                    logger.warning("Skipping invalid event: %s", exc)
            else:
                logger.warning("Skipping unsupported event type: %s", type(item))

        config = self._load_config(context, allow_default=False)
        if config is None:
            config = file_config or SecurityConfig()

        return events, config

    def _load_config(
        self, context: SecurityContext, *, allow_default: bool = True
    ) -> SecurityConfig | None:
        config_data = context.get("config")
        if isinstance(config_data, SecurityConfig):
            return config_data
        if isinstance(config_data, dict):
            try:
                return SecurityConfig(**config_data)
            except Exception as exc:
                logger.warning("Failed to parse config: %s", exc)

        config_file = context.get("config_file")
        if config_file:
            path = Path(config_file)
            if path.exists():
                try:
                    payload = json.loads(path.read_text(encoding="utf-8"))
                    if isinstance(payload, dict):
                        if "config" in payload and isinstance(payload["config"], dict):
                            payload = payload["config"]
                        return SecurityConfig(**payload)
                except Exception as exc:
                    logger.warning("Failed to load config_file: %s", exc)
            else:
                logger.warning("config_file not found: %s", config_file)

        if allow_default:
            return SecurityConfig()
        return None

    def _render_markdown(self, result) -> str:
        flagged_events = [event for event in result.security_report if event.flag]
        lines = [
            "# Security Report",
            "",
            "## Summary",
            f"- Total events: {result.meta.event_count}",
            f"- Critical: {result.meta.critical_count}",
            f"- High: {result.meta.high_count}",
            f"- Medium: {result.meta.medium_count}",
            "",
            "## Incidents",
        ]

        if result.incident_alert:
            for incident in result.incident_alert:
                actions = ", ".join(incident.suggested_action) or "None"
                lines.append(
                    f"- [{incident.severity}] {incident.timestamp} {incident.agent} "
                    f"{incident.event}: {incident.summary} | actions: {actions}"
                )
        else:
            lines.append("- None")

        lines.extend(["", "## Flagged Events"])
        if flagged_events:
            for event in flagged_events:
                flags = ", ".join(flag.code for flag in event.flag) or "None"
                actions = ", ".join(event.suggested_action) or "None"
                lines.append(
                    f"- [{event.priority}] {event.timestamp} {event.agent} "
                    f"{event.event} user={event.user} ip={event.ip} "
                    f"flags: {flags} | actions: {actions}"
                )
        else:
            lines.append("- None")

        lines.extend(["", "## Recurring Risks"])
        if result.recurring_risk:
            for risk in result.recurring_risk:
                lines.append(
                    f"- {risk.event_type} ({risk.status}) x{risk.count}: {risk.message}"
                )
        else:
            lines.append("- None")

        return "\n".join(lines)


__all__ = ["SecurityStep"]
