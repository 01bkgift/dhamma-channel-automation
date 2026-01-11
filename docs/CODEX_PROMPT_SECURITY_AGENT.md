# Codex Prompt: Security Agent - Production Ready

## Objective

ทำให้ **SecurityAgent** สามารถใช้งานได้จริงใน Pipeline Orchestrator และ Test Verified เพื่อเฝ้าระวังความปลอดภัยของระบบ

---

## Current Status

| Component | Status | Location |
|-----------|--------|----------|
| Agent Module | ❌ | `src/agents/security_agent/` (Need Check/Create) |
| Unit Tests | ❌ | `tests/test_security_agent.py` |
| Prompt File | ✅ | `prompts/security_agent_v1.txt` |
| Pipeline Step | ❌ | `src/steps/security.py` |
| Orchestrator Wrapper | ❌ | `orchestrator.py` (Need `run_security_step`) |
| AGENTS Mapping | ❌ | `orchestrator.py` (Need mapping update) |
| Step Tests | ❌ | `tests/steps/test_security_step.py` |
| Smoke Test | ❌ | `pipelines/smoke_security.yaml` |

---

## Definition of Done

1.  **Code Complete**: All planned files (Agent, Model, Step, Tests) are implemented.
2.  **Tests Passing**: Unit tests (logic) and Step Integration tests (wrapper) pass.
3.  **Pipeline Verified**: `smoke_security.yaml` runs successfully using `orchestrator.py`.
4.  **Artifacts**: Generates `security_report.json` (machine) and `security_report.md` (human summary).
5.  **Clean Code**: No linting errors.

## Non-goals

- **Real-time Monitoring**: This is a batch-process agent (runs in pipeline), not a daemon.
- **Auto-mediation**: Suggestions are provided, but automatic blocking is out of scope for v1.

---

## Implementation Plan

### 1. [NEW] `src/agents/security_agent/model.py`

```python
"""
Security Agent Models
"""
from typing import List, Optional, Dict, Literal
from pydantic import BaseModel, Field

class SecurityEvent(BaseModel):
    timestamp: str
    agent: str
    event: str
    user: str
    ip: str
    status: str

class SecurityConfig(BaseModel):
    sensitive_agents: List[str] = Field(default_factory=list)
    monitor_event: List[str] = Field(default_factory=list)
    allowlist_users: List[str] = Field(default_factory=list)
    allowlist_ip_ranges: List[str] = Field(default_factory=list)
    alert_priority: Dict[str, str] = Field(default_factory=dict)

class SecurityInput(BaseModel):
    security_event_log: List[SecurityEvent]
    config: SecurityConfig

class SecurityFlag(BaseModel):
    code: str
    message: str

class AnalyzedEvent(SecurityEvent):
    flag: List[SecurityFlag] = Field(default_factory=list)
    priority: str = "low"
    suggested_action: List[str] = Field(default_factory=list)

class IncidentAlert(BaseModel):
    timestamp: str
    agent: str
    event: str
    severity: str
    summary: str
    recipient: List[str]
    suggested_action: List[str]

class RecurringRisk(BaseModel):
    event_type: str
    status: str
    count: int
    time_window_hours: int
    message: str

class SecurityReportMeta(BaseModel):
    event_count: int
    critical_count: int
    high_count: int
    medium_count: int
    self_check: Dict[str, bool]

class SecurityOutput(BaseModel):
    security_report: List[AnalyzedEvent]
    incident_alert: List[IncidentAlert]
    recurring_risk: List[RecurringRisk]
    meta: SecurityReportMeta
```

### 2. [NEW] `src/agents/security_agent/agent.py`

```python
"""
Security Agent Implementation (Deterministic V1)
"""
from typing import List
from .model import (
    SecurityInput, SecurityOutput, 
    AnalyzedEvent, SecurityFlag, IncidentAlert, 
    RecurringRisk, SecurityReportMeta
)

class SecurityAgent:
    def run(self, input_data: SecurityInput) -> SecurityOutput:
        analyzed_events = []
        incidents = []
        recurring_tracker = {} # (event, status) -> count
        
        cfg = input_data.config
        
        # 1. Analyze each event
        for event in input_data.security_event_log:
            flags = []
            priority = "low"
            actions = []
            
            # Rule: Unknown User/IP
            if (event.user == "unknown" or 
                (cfg.allowlist_users and event.user not in cfg.allowlist_users)):
                flags.append(SecurityFlag(code="suspicious_access", message="Unknown or unauthorized user"))
                priority = "critical"
                actions.append("Block IP")
            
            # Rule: Auth Fail
            if event.event == "auth_fail" or (event.event == "api_key_access" and event.status == "failed"):
                flags.append(SecurityFlag(code="auth_fail", message="Authentication failed"))
                if priority != "critical": priority = "high" # Elevate to high/critical
                
            # Rule: Sensitive Agent Elevation
            if event.agent in cfg.sensitive_agents:
                 # Logic to bump priority (low->medium, medium->high, high->critical)
                 priority = self._elevate_priority(priority)

            # Create Analyzed Event
            analyzed = AnalyzedEvent(
                **event.model_dump(),
                flag=flags,
                priority=priority,
                suggested_action=actions
            )
            analyzed_events.append(analyzed)
            
            # Create Incident if Critical/High
            if priority in ["critical", "high"] and flags:
                incidents.append(IncidentAlert(
                    timestamp=event.timestamp,
                    agent=event.agent,
                    event=event.event,
                    severity=priority,
                    summary=f"Flagged {priority}: {flags[0].message}",
                    recipient=["admin"],
                    suggested_action=actions
                ))

            # Track for recurring
            key = (event.event, event.status)
            recurring_tracker[key] = recurring_tracker.get(key, 0) + 1

        # 2. Check Recurring Risks
        recurring_risks = []
        for (evt_type, status), count in recurring_tracker.items():
            if count >= 2:
                recurring_risks.append(RecurringRisk(
                    event_type=evt_type,
                    status=status,
                    count=count,
                    time_window_hours=24,
                    message=f"Event {evt_type} ({status}) occurred {count} times"
                ))

        # 3. Meta
        critical_count = sum(1 for e in analyzed_events if e.priority == "critical")
        high_count = sum(1 for e in analyzed_events if e.priority == "high")
        
        return SecurityOutput(
            security_report=analyzed_events,
            incident_alert=incidents,
            recurring_risk=recurring_risks,
            meta=SecurityReportMeta(
                event_count=len(analyzed_events),
                critical_count=critical_count,
                high_count=high_count,
                medium_count=0, # TODO implement medium count logic
                self_check={"all_sections_present": True, "no_empty_fields": True}
            )
        )

    def _elevate_priority(self, p: str) -> str:
        order = ["low", "medium", "high", "critical"]
        try:
            idx = order.index(p)
            new_idx = min(idx + 1, 3)
            return order[new_idx]
        except ValueError:
            return p
```

### 3. [NEW] `src/steps/security.py`

```python
"""
Security Pipelin Step
"""
import json
from pathlib import Path
from automation_core.base_step import BaseStep
from agents.security_agent.agent import SecurityAgent
from agents.security_agent.model import SecurityInput, SecurityConfig, SecurityEvent

class SecurityStep(BaseStep):
    def __init__(self):
        super().__init__("security", "Security", "1.0.0")
        self.agent = SecurityAgent()

    def execute(self, context: dict) -> dict:
        # Resolve Input File (log)
        # Supports reading from previous step output or direct list
        events_data = []
        # ... logic to load events from context['input_log_file'] or context['events'] ...
        
        # Load Config
        # ... logic to load config ...
        
        # Run Agent
        inp = SecurityInput(security_event_log=events_data, config=config_data)
        result = self.agent.run(inp)
        
        # Save Output
        # ... save security_report.json ...
        # ... generate and save security_report.md ...

        return {"status": "success", "report_file": "..."}
```

### 4. Integration - `orchestrator.py`

- Add `run_security_step` wrapper.
- Update `AGENTS` mapping: `"Security": run_security_step`.

### 5. Verification

#### Unit Tests
```python
# tests/test_security_agent.py
def test_detect_unknown_user():
    # ... mock input with user="hacker" ...
    # ... assert priority="critical" ...
```

#### Smoke Test `pipelines/smoke_security.yaml`
```yaml
pipeline: smoke-security
steps:
  - id: security_check
    uses: Security
    input:
      events:
        - timestamp: "2025-01-01T10:00:00Z"
          agent: "Integration"
          event: "api_key_access"
          user: "unknown" # Should trigger critical
          ip: "1.2.3.4"
          status: "failed"
      config:
        sensitive_agents: ["Integration"]
```

#### Run Verification

**PowerShell:**
```powershell
pytest tests/test_security_agent.py
python orchestrator.py run pipelines/smoke_security.yaml
Get-Content output/artifacts/security_report.json | ConvertFrom-Json
```
