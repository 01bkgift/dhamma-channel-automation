# REFERENCED ARTIFACT: Codex Prompt — DoctrineValidator Step (Production-Ready)

## ROLE
You are implementing a single production PR that makes DoctrineValidator fully runnable inside the existing Orchestrator with no change to pipeline semantics or order.

This is integration + hardening only.
No new product features. No refactor beyond scope.

## OBJECTIVE
Make DoctrineValidator operate as a first-class pipeline step that:

1.  Conforms exactly to BaseStep.execute(context) -> dict contract
2.  Works with the current Orchestrator runner + wrapper pattern
3.  Produces deterministic, auditable artifacts under `output/<run_id>/artifacts/`
4.  Passes unit + step + smoke tests

## NON-GOALS (ABSOLUTE)
- ❌ Do NOT change pipeline order
- ❌ Do NOT modify existing runtime semantics
- ❌ Do NOT add configuration keys beyond those specified
- ❌ Do NOT introduce async, retries, caching, or platform abstractions
- ❌ Do NOT write files outside output/<run_id>/artifacts/
- ❌ Do NOT require secrets or environment variables

## ALLOWED FILES (STRICT)
You may only create or modify the files listed below.

**CREATE**
- `src/steps/doctrine_validator.py`
- `tests/steps/test_doctrine_validator_step.py`
- `pipelines/smoke_doctrine_validator.yaml`

**MODIFY**
- `src/steps/__init__.py`
- `orchestrator.py`

*No other files may be touched.*

## STEP CONTRACT (MUST MATCH EXACTLY)

### Base Class
All logic must live inside:

```python
class DoctrineValidatorStep(BaseStep):
    def execute(self, context: dict) -> dict:
        ...
```

### Context (input)
Provided by Orchestrator wrapper:

```python
context = {
  "script_file": "<resolved path or empty>",
  "passages_file": "<resolved path or empty>",
  "output_dir": "output/<run_id>/artifacts",
  # optional config:
  "strictness": "normal" | "strict",
  "check_sensitive": bool,
  "ignore_segments": list[int]
}
```

### Output (success)
execute() MUST return:

```python
{
  "status": "success",
  "output_file": "<path to script_validated.md>",
  "report_file": "<path to validation_report.json>",
  "summary": {...},
  "recommend_rewrite": bool,
  "ok_ratio": float,
  "citation_coverage": float,
  "warnings": list[str]
}
```

### Output (error — fail-closed)
No exceptions inside execute.
Return:

```python
{
  "status": "error",
  "error": "<reason code + message>"
}
```
Wrapper is the only place allowed to raise.

## BEHAVIOR REQUIREMENTS

1.  **Input Resolution**
    - `script_file` must exist
    - Accept .json (preferred) or .md
    - If neither script nor passages exist → error

2.  **Passages Validation (Fail-Closed)**
    - `_get_passages()` MUST return None if both primary and supportive are empty
    - This must result in status="error"

3.  **ignore_segments**
    - If ignore_segments removes all segments → error
    - Partial ignore is allowed and reflected in summary totals

4.  **Output Files (Deterministic)**
    - Always write exactly two files into output_dir:
        - `script_validated.md`: Pass-through original script. Add deterministic HTML comment header/footer with validation status, strictness, summary counts.
        - `validation_report.json`: Use result.model_dump(). Serialize with `json.dump(data, f, ensure_ascii=False, indent=2, sort_keys=True)`.
    - No timestamps in filenames.
    - No randomness.
    - No writing elsewhere.

5.  **Logging (SOC2-safe)**
    - Allowed: counts, ratios, file paths
    - Forbidden: full script text, passage content

## ORCHESTRATOR INTEGRATION

### Wrapper Function

Implement:
`def run_doctrine_validator_step(step: dict, run_dir: Path) -> Path:`

Responsibilities:
1.  Resolve input_from against: `run_dir/`, `run_dir/artifacts/`, `.json` before `.md`
2.  Inject `output_dir = run_dir / "artifacts"`
3.  Call `DoctrineValidatorStep().execute(context)`
4.  If success → return Path(output_file)
5.  If error → raise RuntimeError(...)

### AGENTS Mapping
Replace `"DoctrineValidator": agent_doctrine_validator` with `"DoctrineValidator": run_doctrine_validator_step`

## TEST REQUIREMENTS (MANDATORY)

### Step Tests
`tests/steps/test_doctrine_validator_step.py` must cover:
- success with direct context input
- success with script_file + passages_file
- output filename = script_validated.md
- empty passages → error
- missing script → error
- ignore all segments → error
- ignore partial segments → reduced totals
- no files written outside output_dir

### Smoke Pipeline
`pipelines/smoke_doctrine_validator.yaml`
- Standalone
- Inline script + passages
- No secrets
- Produces both artifacts under output/<run_id>/artifacts/

## VERIFICATION (MUST RUN)
Before creating PR, you must run and confirm:
1.  `pytest tests/steps/test_doctrine_validator_step.py`
2.  `python orchestrator.py run pipelines/smoke_doctrine_validator.yaml`

PR body must include:
- commands run
- confirmation that artifacts exist under correct path
- confirmation that no pipeline order was changed
