# PR13: Lean Notifications (Webhook Notify)

## Summary

Added `notify.webhook` step to the pipeline. This step sends a lean, deterministic, and safe notification to configured webhooks (e.g., Discord, LINE) after the `decision.support` step completes.

## Changes

- **New Step**: `src/steps/notify_webhook/` module
- **Contract**: Added `docs/contracts/notify_summary_v1.md` (v1 schema)
- **Integration**: Added `notify.webhook` step to `video_complete.yaml` and `youtube_upload_smoke_requires_quality.yaml`
- **Orchestrator**: Registered `notify.webhook` in `AGENTS` map

## Security

- ✅ **No Secrets Committed**: Webhook URLs are sourced STRICTLY from `NOTIFY_WEBHOOKS_JSON` environment variable.
  Example: `[{"name":"ops","url":"https://discord.com/api/webhooks/..."}]` (Raw URL only)
- ✅ **Redaction**: All URLs in logs and artifacts are redacted (e.g., `https://discord.com/***oken`).
- ✅ **Safe Defaults**: `NOTIFY_ENABLED` defaults to `false`.

## Testing

- **Unit Tests**: `pytest tests/steps/notify_webhook/` (12 tests passed) (Mocked network calls)
- **Determinism**: Verified `message_digest` remains constant for identical content across different runs (timestamp excluded).
- **Fail-Open**: Confirmed step does not block pipeline on HTTP errors or timeouts (unless configured otherwise).

## Runtime Impact

- **Default**: No impact (`skipped` status).
- **Enabled**: Uses Python stdlib `urllib` (no new dependencies).
- **Performance**: Sequential execution with 3s timeout per target (max 10 targets).

## Verification

See `walkthrough.md` for detailed verification results and example artifacts.
