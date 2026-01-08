# PR14: Add YouTube AI content policy (anti-reuse, human-value) — docs-only

## Summary

เพิ่มเอกสารนโยบายอย่างเป็นทางการสำหรับการผลิต YouTube content ด้วย AI  
เป็นไปตาม YouTube Partner Program policies และ ISO 27001 / SOC2 Type II controls

## Changes

- ✅ **Docs-only** — ไม่มีการแก้ไข runtime/pipeline/CI
- ✅ **Policy version 1.0.0** พร้อม versioning scheme และ effective date
- ✅ **Deterministic human-in-the-loop** — บังคับ ≥2 จาก 5 human contributions
- ✅ **Content Risk Matrix** — Green/Yellow/Red พร้อม Required Human %
- ✅ **Anti-spam upload limits** — 2/day, 4hr gap, 7/week ชัดเจน
- ✅ **Violation classification** — CRITICAL/MAJOR/MINOR + escalation path
- ✅ **SOC2-aligned audit trail** — mapping กับ existing artifacts

## Files Changed

| Path | Type | Description |
|------|------|-------------|
| `docs/CONTENT_POLICY_YOUTUBE_AI.md` | NEW | นโยบาย YouTube AI Content Policy (15 sections) |

## Key Policy Sections

1. **Non-negotiables (Hard Rules)** — 12 กฎเหล็กด้วย SHALL NOT
2. **Human-in-the-Loop Requirements** — ≥2 touchpoints + approval authority
3. **Content Risk Matrix** — Green/Yellow/Red พร้อมเงื่อนไขและ % ชัดเจน
4. **Script Structure Standard** — 5-part template พร้อม AI limit %
5. **Upload Pattern Anti-Spam** — ตัวเลขเฉพาะเจาะจง
6. **Pre-Publish Checklist** — Copy/paste ready
7. **Enforcement & Violations** — 3 levels + escalation path + exception process
8. **Audit Trail Mapping** — Reference existing artifacts (ไม่แก้ไข schema)
9. **Policy Maintenance** — 90-day review cadence + changelog

## Verification

- [x] Only `docs/CONTENT_POLICY_YOUTUBE_AI.md` changed
- [x] No runtime/pipeline/CI changes
- [x] Deterministic wording (MUST/MUST NOT/SHALL/SHALL NOT)
- [x] ตัวเลขชัดเจน (ไม่มี "ประมาณ", "maybe")
- [x] Evidence Mapping table อ้างอิง existing artifacts ที่มีจริง
- [x] No secrets or operational endpoints

## ISO/SOC2 Compliance

- ✅ Policy versioning + effective date
- ✅ Document ownership + backup owner
- ✅ Review cadence (90 days)
- ✅ Audit trail requirements
- ✅ Exception approval process

## Related

- ไม่มี code changes ใน PR นี้
- เอกสารนี้เป็น "policy anchor" สำหรับ reference ในอนาคต
