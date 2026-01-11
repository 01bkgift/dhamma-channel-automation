# Codex Prompt: ScriptWriter Agent - Production Ready

## Objective

ทำให้ **ScriptWriterAgent** สามารถใช้งานได้จริงใน Pipeline Orchestrator และ Test Verified

---

## Current Status

| Component | Status | Location |
|-----------|--------|----------|
| Agent Module | ✅ | `src/agents/script_writer/` |
| Unit Tests | ✅ | `tests/test_script_writer_agent.py` |
| Prompt File | ✅ | `prompts/script_writer_v1.txt` |
| Pipeline Step | ✅ | `src/steps/script_writer.py` |
| Orchestrator Wrapper | ✅ | `orchestrator.py` (Search `run_script_writer_step`) |
| AGENTS Mapping | ✅ | `orchestrator.py` (Search `AGENTS` mapping) |
| Step Tests | ✅ | `tests/steps/test_script_writer_step.py` |
| Smoke Test | ✅ | `pipelines/smoke_script_writer.yaml` |

---

## Definition of Done

1.  **Code Complete**: All planned files (`src/steps/script_writer.py`, tests, pipelines) are implemented.
2.  **Tests Passing**: Unit tests and Step Integration tests pass.
3.  **Pipeline Verified**: `smoke_script_writer.yaml` runs successfully using `orchestrator.py`.
4.  **Artifacts**: Generates `script.md` (human) and `script.json` (machine) in the correct output directory.
5.  **Clean Code**: No linting errors (Ruff/Black).

## Non-goals

- **LLM Integration**: For v1, we use deterministic logic. LLM integration via `prompt_loader` is a future enhancement.
- **Complex Audio Directives**: Focus on text script first.

---

## Implementation Details

### 1. `src/steps/script_writer.py`

(Implemented)
Wraps `ScriptWriterAgent` to accept `outline_file` and `passages_file` from context or artifacts, producing `script.md` and `script.json`.

### 2. `orchestrator.py` Integration

(Implemented)
- Added `run_script_writer_step` wrapper function to handle file path resolution.
- Updated `AGENTS` dictionary to map `"ScriptWriter"` to `run_script_writer_step`.

### 3. Verification & Tests

#### Unit & Integration Tests

**Bash:**
```bash
pytest tests/test_script_writer_agent.py -xvs
pytest tests/steps/test_script_writer_step.py -xvs
```

**PowerShell:**
```powershell
pytest tests/test_script_writer_agent.py -xvs
pytest tests/steps/test_script_writer_step.py -xvs
```

#### Smoke Pipeline

**Bash:**
```bash
python orchestrator.py run pipelines/smoke_script_writer.yaml
```

**PowerShell:**
```powershell
python orchestrator.py run pipelines/smoke_script_writer.yaml
```

#### Output Verification

Check that files are generated:

**Bash:**
```bash
ls -la output/artifacts/
cat output/artifacts/script.md
jq '.topic, .segment_count' output/artifacts/script.json
```

**PowerShell:**
```powershell
Get-ChildItem output/artifacts/
Get-Content output/artifacts/script.md
Get-Content output/artifacts/script.json | ConvertFrom-Json | Select-Object topic, segment_count
```

---

## Key Design Decisions

1.  **Output Format**: `script.md` (matches `video.yaml`) + `script.json` (machine).
2.  **Schema Validation**: Tests use `ScriptOutlineAgent` to generate valid outline inputs.
3.  **input_from Support**: Wrapper handles `outline.md` equivalent (looking for corresponding `.json`).
