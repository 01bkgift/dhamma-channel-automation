# Notify Summary Contract (v1)

**Artifact**: `output/<run_id>/artifacts/notify_summary.json`  
**Schema Version**: `v1`

## Purpose

Records the result of the `notify.webhook` step, including which targets were attempted, the status of each, and any reason codes for skipping or failure. This artifact is produced even if the notification is skipped or fails.

## Schema

```json
{
  "schema_version": "v1",
  "run_id": "<string>",
  "timestamp_utc": "<ISO8601 string>",
  "notification_status": "sent" | "failed" | "skipped",
  "targets_attempted": [
    {
      "name": "<string: target name from config>",
      "url_redacted": "<string: scheme://domain/***last4>",
      "result": "success" | "error" | "timeout",
      "http_status": <int | null>
    }
  ],
  "message_digest": "<string: sha256 of message body excluding timestamp>",
  "reason_codes": [
    "<string: reason code>"
  ]
}
```

## Field Descriptions

- **`schema_version`**: Must be `"v1"`.
- **`run_id`**: The ID of the current pipeline run.
- **`timestamp_utc`**: Execution time in ISO8601 UTC.
- **`notification_status`**:
  - `"sent"`: At least one target succeeded.
  - `"failed"`: All targets failed (or fatal error).
  - `"skipped"`: Notification disabled or prerequisites not met.
- **`targets_attempted`**: List of targets processed. Order matches `NOTIFY_WEBHOOKS_JSON`.
  - `name`: Name from configuration.
  - `url_redacted`: Safe version of URL. Format: `<scheme>://<domain>/***<last4>`.
  - `result`: Outcome for this specific target.
  - `http_status`: HTTP status code (e.g., 200, 404, 500) or null if no response (timeout/connection error).
- **`message_digest`**: SHA256 hash of the message body *excluding* any timestamps. Ensures determinism.
- **`reason_codes`**: List of strings explaining the status.

## Reason Codes

| Code | Meaning |
|------|---------|
| `WEBHOOK_DISABLED` | `NOTIFY_ENABLED` != `"true"` |
| `NO_TARGETS` | `NOTIFY_WEBHOOKS_JSON` missing or empty |
| `MISSING_DECISION` | `decision_support_summary.json` is missing |
| `INVALID_CONFIG` | `NOTIFY_WEBHOOKS_JSON` is malformed or invalid |
| `HTTP_ERROR` | Received HTTP 4xx or 5xx response |
| `TIMEOUT` | Request timed out |
| `CONNECTION_ERROR` | Network/DNS/TLS error |

## Example

```json
{
  "schema_version": "v1",
  "run_id": "run-12345",
  "timestamp_utc": "2024-01-01T12:00:00Z",
  "notification_status": "sent",
  "targets_attempted": [
    {
      "name": "discord_ops",
      "url_redacted": "https://discord.com/***xyz1",
      "result": "success",
      "http_status": 204
    }
  ],
  "message_digest": "a1b2c3d4...",
  "reason_codes": []
}
```
