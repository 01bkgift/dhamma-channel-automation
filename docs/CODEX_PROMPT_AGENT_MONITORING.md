# Codex Prompt — Agent Monitoring (Production-Ready, Final)

## ROLE
You are implementing a single, production-grade PR that creates the Agent Monitoring pipeline step (Health Check / Pre-flight).

This step is a one-shot guardian that validates environment readiness before expensive agents execute.

## OBJECTIVE
Implement AgentMonitoringStep that:

1.  **Validates System Resources**
    - Disk space
    - Memory availability
2.  **Verifies Configuration Safety**
    - .env / prod.env presence
    - Required secrets exist and are non-empty (never log values)
3.  **Strictly Conforms to BaseStep**
    - execute(context: dict) -> dict
4.  **Produces Deterministic Artifacts**
    - Exactly two files, fixed names, deterministic content
5.  **Is Fully Test-Verified**
    - Unit tests, step tests, smoke pipeline

## NON-GOALS (ABSOLUTE — MUST NOT DO)
- ❌ No continuous monitoring loop (one-shot only)
- ❌ Do NOT fix detected issues (report only)
- ❌ Do NOT install dependencies
- ❌ Do NOT require internet access
- ❌ Do NOT change pipeline order or semantics

## ALLOWED FILES (STRICT)
**CREATE**
- `src/steps/agent_monitoring.py`
- `tests/steps/test_agent_monitoring_step.py`
- `pipelines/smoke_agent_monitoring.yaml`

**MODIFY**
- `src/steps/__init__.py`
- `orchestrator.py` (step registration only)

*No other files may be touched.*

## STEP CONTRACT (MUST MATCH EXACTLY)

### Base Class
```python
class AgentMonitoringStep(BaseStep):
    def execute(self, context: dict) -> dict:
        ...
```

### Context (Input)
Provided by orchestrator wrapper:

```python
context = {
    "output_dir": "output/<run_id>/artifacts",

    # optional config (defaults apply if missing)
    "check_disk_space": True,
    "min_disk_GB": 2,
    "check_memory": True,
    "required_secrets": ["YOUTUBE_API_KEY"]
}
```

## STATUS SEMANTICS (UNAMBIGUOUS)

### SUCCESS
Return "status": "success" only if:
- All enabled checks pass
- No issues detected

### WARNING (NON-CRITICAL FAILURES)
Return "status": "warning" if any of the following occur:
- Disk space below threshold
- Memory below safe threshold
- Required secret is missing or empty
- Optional check skipped due to missing dependency (e.g. psutil)
- ⚠️ Warnings must NOT crash the pipeline

### ERROR (FAIL-CLOSED)
Return "status": "error" only for usage / contract errors, such as:
- Invalid context types
- Non-parsable configuration
- Unable to write output artifacts
- ❌ Resource or config problems are NOT errors

## OUTPUT CONTRACT (SUCCESS or WARNING)
execute() MUST return:

```python
{
  "status": "success" | "warning",
  "output_file": "<output_dir>/monitoring_summary.md",
  "report_file": "<output_dir>/monitoring_report.json",
  "checks": {
      "system": bool,
      "config": bool,
      "resources": bool
  },
  "issues": list[str]
}
```

### Issues Format (Deterministic)
Each issue MUST follow: `<CODE>: <human-readable description>`

Examples:
- `LOW_DISK_SPACE: available=1.4GB required=2GB`
- `MISSING_SECRET: YOUTUBE_API_KEY`
- `RESOURCE_CHECK_SKIPPED: psutil_not_installed`

## OUTPUT FILES (DETERMINISTIC)

### 1. monitoring_summary.md
- Human-readable
- Uses emojis only: ✅ ⚠️ ❌
- No timestamps
- No secrets

### 2. monitoring_report.json
- Machine-readable
- `json.dump(..., sort_keys=True, ensure_ascii=False)`
- No secrets
- No timestamps

## RESOURCE CHECK RULES

### Disk
- Use `shutil.disk_usage`
- Compare against `min_disk_GB`

### Memory
- Prefer `psutil`
- If unavailable:
    - Mark check as passed
    - Add warning issue: `RESOURCE_CHECK_SKIPPED`

## CONFIGURATION CHECK RULES

### Env File
- Check existence in priority order:
    1. `prod.env`
    2. `.env`
- If either exists → OK
- If neither exists → WARNING

### Secrets
- Secret is present if:
    - Key exists in env
    - Value is non-empty string
- NEVER log secret values
- Missing secret → WARNING (not error)

## LOGGING (SOC2-SAFE)
- Allowed: "Secret YOUTUBE_API_KEY is present"
- Forbidden: "Secret YOUTUBE_API_KEY=AIzaSy..."

## ORCHESTRATOR INTEGRATION

### Wrapper Function
Implement:
`def run_agent_monitoring_step(step: dict, run_dir: Path) -> Path:`

Responsibilities:
1. Inject `output_dir = run_dir / "artifacts"`
2. Call `AgentMonitoringStep().execute(context)`
3. If status is success or warning → return output_file
4. If status is error → raise RuntimeError

### AGENTS Mapping
Add: `"AgentMonitoring": run_agent_monitoring_step`

## TEST REQUIREMENTS (MANDATORY)

### Step Tests
`tests/steps/test_agent_monitoring_step.py` must cover:
- All checks passing → success
- Low disk → warning
- Missing secret → warning
- psutil missing → warning
- Deterministic output files
- No secret leakage in outputs

### Smoke Pipeline
`pipelines/smoke_agent_monitoring.yaml`
- Standalone
- Minimal config
- Produces both artifacts

## VERIFICATION (MUST RUN BEFORE PR)
1. `pytest tests/steps/test_agent_monitoring_step.py`
2. `python orchestrator.py run pipelines/smoke_agent_monitoring.yaml`

PR body MUST include:
- Commands executed
- Confirmation of artifact creation paths
