# PR14.3: VPS Production Runbook + Deploy Templates (docs-first)

## Summary

**Docs-only PR** — เพิ่ม production runbook และ deploy templates สำหรับ VPS deployment

ไม่มีการเปลี่ยนแปลง runtime, pipeline, CI/CD, หรือ code ใดๆ

---

## Files Added

### Documentation (4 files)

| File | Purpose |
|------|---------|
| `docs/RUNBOOK_VPS_PRODUCTION.md` | Single source of truth สำหรับ deploy/operate/recover |
| `docs/DEPLOYMENT_FLOWBIZ_VPS.md` | VPS deployment overview + architecture |
| `docs/OPS_CHECKLIST.md` | Daily/weekly/monthly ops checklist |
| `docs/SECURITY_DEPLOYMENT_NOTES.md` | SOC2/ISO security notes |

### Templates (4 files)

| File | Purpose |
|------|---------|
| `docs/templates/env.production.example` | Production .env template (placeholders only) |
| `docs/templates/nginx.site.conf.example` | Nginx config template |
| `docs/templates/deploy_manual.sh.example` | Manual deploy script for operators |
| `docs/templates/rollback_manual.sh.example` | Manual rollback script |

### Updated (1 file)

| File | Change |
|------|--------|
| `docs/DEPLOYMENT.md` | Added links to new VPS production docs |

---

## What Operators Gain

1. **RUNBOOK_VPS_PRODUCTION.md**
   - Step-by-step deploy instructions
   - STOP conditions at each step
   - Approval gate operations
   - Soft-live mode documentation
   - Rollback procedures
   - Recovery procedures
   - Audit/SOC2 guidance

2. **Templates**
   - Copy-paste ready for VPS setup
   - Clear REPLACE markers
   - No secrets (placeholders only)
   - Tested against actual repo structure

3. **Ops Checklist**
   - Daily health checks
   - Weekly disk/log review
   - Monthly compliance tasks

---

## Explicit Non-Goals

| ❌ NOT included | Reason |
|-----------------|--------|
| Runtime code changes | Docs-only PR |
| Pipeline modifications | Out of scope |
| CI/CD automation | Manual deploy only |
| Systemd service files | Docker restart policy used |
| Secrets/credentials | Security |
| SSH access scripts | Infra responsibility |
| Log aggregation setup | Separate concern |
| DNS/Domain config | Infra responsibility |
| Firewall rules | Assumes pre-configured |

---

## Verification

- [ ] All commands tested on Ubuntu 20.04+
- [ ] All file references verified to exist in repo
- [ ] No secrets in any file
- [ ] Health endpoint is `/healthz` (verified)
- [ ] Meta endpoint is `/v1/meta` (verified)
- [ ] Port config uses `config/flowbiz_port.env` (verified)

---

## Checklist

- [x] Docs-only (no code changes)
- [x] No secrets in diff
- [x] Thai language with English commands
- [x] All paths verified against repo
- [x] Templates use `<PLACEHOLDER>` format
