# FlowBiz VPS Deployment Overview

> สรุปภาพรวมการ deploy dhamma-channel-automation บน FlowBiz VPS

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│                              VPS HOST                                     │
│                                                                          │
│  ┌────────────────┐    ┌────────────────┐    ┌────────────────────────┐  │
│  │   System       │    │   Docker       │    │   Application          │  │
│  │   Nginx        │───▶│   Container    │───▶│   /opt/flowbiz-client- │  │
│  │   :80/:443     │    │   :3007        │    │   dhamma               │  │
│  └────────────────┘    └────────────────┘    └────────────────────────┘  │
│         │                     │                        │                  │
│         │                     │                        ├── data/          │
│         │                     │                        ├── output/        │
│  TLS termination       127.0.0.1 only                  └── logs/          │
│  (Let's Encrypt)       (no public exposure)                               │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Key Components

### 1. System Nginx (Host Level)

| Property | Value |
|----------|-------|
| Location | `/etc/nginx/sites-available/flowbiz-client-dhamma.conf` |
| Template | `nginx/flowbiz-client-dhamma.conf` |
| Ports | 80 (HTTP), 443 (HTTPS) |
| Upstream | `127.0.0.1:${FLOWBIZ_ALLOCATED_PORT}` |
| TLS | Let's Encrypt via certbot |

### 2. Docker Container

| Property | Value |
|----------|-------|
| Image | Built from `Dockerfile` |
| Container name | `dhamma-web` |
| Internal port | 8000 |
| Host binding | `127.0.0.1:${FLOWBIZ_ALLOCATED_PORT}:8000` |
| Restart policy | `unless-stopped` |

### 3. Application

| Property | Value |
|----------|-------|
| Path | `/opt/flowbiz-client-dhamma` |
| Framework | FastAPI |
| Health endpoint | `/healthz` |
| Meta endpoint | `/v1/meta` |

---

## Port Configuration

**Single Source of Truth:** `config/flowbiz_port.env`

```bash
FLOWBIZ_ALLOCATED_PORT=3007
```

> [!IMPORTANT]
> ต้องใช้ `--env-file config/flowbiz_port.env` กับทุกคำสั่ง docker compose

---

## Directory Structure

```
/opt/flowbiz-client-dhamma/
├── .env                          # Production environment (ห้าม commit)
├── config/
│   └── flowbiz_port.env          # Port allocation
├── data/                         # Application data
├── output/                       # Pipeline outputs
│   └── <run_id>/
│       ├── artifacts/            # Approval gate summaries
│       └── control/              # Cancel decisions
├── nginx/
│   └── flowbiz-client-dhamma.conf    # Nginx template
├── docker-compose.yml
└── scripts/
    ├── runtime_verify.sh         # Deploy verification
    └── guardrails.sh             # Compliance checks
```

---

## Network Flow

```
Internet → Nginx (:443) → Docker (:3007) → App (:8000)
              │
              └── TLS termination
                  Reverse proxy to 127.0.0.1:3007
```

**Security Rules:**

- ✅ Container binds to `127.0.0.1` only
- ✅ No `0.0.0.0` exposure
- ✅ All public traffic via nginx
- ✅ TLS managed by Let's Encrypt

---

## Endpoints

| Endpoint | Purpose | Auth Required |
|----------|---------|---------------|
| `/healthz` | Health check | No |
| `/v1/meta` | Service metadata | No |
| `/` | Application | Yes (if configured) |

### Health Check Response

```json
{
  "status": "ok",
  "service": "flowbiz-client-dhamma",
  "version": "1.0.0"
}
```

### Meta Response

```json
{
  "service": "flowbiz-client-dhamma",
  "environment": "production",
  "version": "1.0.0",
  "build_sha": "abc123"
}
```

---

## Quick Reference Commands

### Start Service

```bash
cd /opt/flowbiz-client-dhamma
docker compose --env-file config/flowbiz_port.env up -d
```

### Check Status

```bash
docker compose --env-file config/flowbiz_port.env ps
source config/flowbiz_port.env
curl -fsS "http://127.0.0.1:${FLOWBIZ_ALLOCATED_PORT}/healthz"
```

### View Logs

```bash
docker compose --env-file config/flowbiz_port.env logs -f
```

### Restart

```bash
docker compose --env-file config/flowbiz_port.env restart
```

### Stop

```bash
docker compose --env-file config/flowbiz_port.env down
```

---

## Related Docs

- [RUNBOOK_VPS_PRODUCTION.md](./RUNBOOK_VPS_PRODUCTION.md) — Full production runbook
- [OPS_CHECKLIST.md](./OPS_CHECKLIST.md) — Daily/weekly checklist
- [SECURITY_DEPLOYMENT_NOTES.md](./SECURITY_DEPLOYMENT_NOTES.md) — Security notes
- [DEPLOYMENT.md](./DEPLOYMENT.md) — General deployment guide
