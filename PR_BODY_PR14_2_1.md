# PR14.2.1: Collision-Safe Fake Video ID

## Problem

Current Fake Video ID generation uses only `title + mode`, which can collide when:

- Same title is reused with different content
- Minor content edits keep title unchanged

This PR strengthens identity determinism without changing behavior or adding features.

## Solution

### 1. **Title Normalization**

- Unicode NFKC normalization
- Whitespace stripping and collapsing  
- Lowercase conversion
- **Why**: Ensures consistent hashing regardless of input variations

### 2. **Content Fingerprint Extraction**

Priority fallback chain:

1. `video_render_summary.json` → `text_sha256_12`
2. `metadata.json` → hash(title + description)
3. `script.json` → hash(entire script)
4. Legacy behavior (title + mode only)

**Why**: Prevents ID collisions when same title used with different content

### 3. **Updated Fake ID Generation**

Canonical payload:

```json
{
  "title": "<normalized>",
  "mode": "<soft_live_mode>",
  "fingerprint": "<artifact_hash>"
}
```

- Deterministic JSON serialization (`sort_keys=True`)
- SHA256 hash → first 16 hex chars
- Format: `soft-live-dry-{digest}`

---

## Changes

### Modified Files (Surgical Changes Only)

- `src/automation_core/youtube_upload.py`: 3 helpers added, 1 function updated
- `tests/steps/soft_live_enforce/test_soft_live_step.py`: 6 new tests

### Diff Summary

```
2 files changed, 240 insertions(+), 7 deletions(-)
```

---

## Testing

### New Tests (6 added)

✅ `test_normalization`: Unicode/whitespace/case handling  
✅ `test_fake_id_with_fingerprint`: Collision prevention  
✅ `test_fake_id_same_content_same_id`: Idempotency  
✅ `test_fake_id_artifact_priority`: Fallback order  
✅ `test_fake_id_missing_artifacts_legacy_fallback`: Graceful degradation  
✅ `test_fake_id_normalization_matters`: Normalization correctness

### Results

```bash
pytest tests/steps/soft_live_enforce/ -v
# 15 passed in 1.57s

pytest (full suite)
# 396 passed in 12.04s
```

**No regressions detected** ✅

---

## Guarantees

1. ✅ **Same content → same ID**: Idempotent across runs
2. ✅ **Different content → different ID**: Collision prevention
3. ✅ **No behavior change when SOFT_LIVE_ENABLED=false**
4. ✅ **Deterministic**: No timestamps, randomness, or run_id used
5. ✅ **Minimal diff**: Surgical changes only, no scope expansion

---

## Compliance

- **ISO/SOC2**: Audit-friendly determinism
- **No new configs**: Uses existing artifacts only
- **Backward compatible**: Legacy behavior when artifacts missing
- **Code quality**: All ruff checks passed

---

## Review Notes

This is a **surgical fix** to strengthen identity determinism. No new features or behavior changes.

**Files touched**: Only 2 files (as per CODEX PROMPT scope)  
**Scope**: Strictly collision prevention, no expansion
