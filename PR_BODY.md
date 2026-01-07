สรุป

เพิ่มเอกสารและการตั้งค่าการปกครอง repository (Governance) เพื่อให้เป็นไปตามมาตรฐาน ISO/SOC2 ขั้นต้น

การเปลี่ยนแปลงหลัก (ไฟล์ที่เพิ่ม/แก้ไข):
- .github/SECURITY.md
- .github/CODEOWNERS
- .github/ISSUE_TEMPLATE/bug_report.md
- .github/ISSUE_TEMPLATE/feature_request.md
- docs/GOVERNANCE.md
- docs/GOVERNANCE_AUDIT.md
- docs/CHANGELOG.md
- CODE_OF_CONDUCT.md
- CONTRIBUTING.md
- ปรับปรุง docs/BASELINE.md

เหตุผล

- เติมช่องว่างด้านนโยบายความปลอดภัย การมอบหมายผู้รับผิดชอบโค้ด และขั้นตอนการควบคุมการเปลี่ยนแปลง
- ไม่แก้ไขโค้ด runtime ใดๆ (ตามขอบเขตที่ตกลง)

ข้อพิสูจน์การทดสอบ (local run outputs)

- Ruff lint: All checks passed!
```
All checks passed!
```

- Ruff format status (local):
```
174 files already formatted
```

- Pytest: ทั้งหมดผ่าน
```
===================== 342 passed in 54.40s =====================
```

เอกสารตรวจสอบเพิ่มเติม

- รายงาน audit: docs/GOVERNANCE_AUDIT.md
- Snapshot (ไม่ commit โดยค่าเริ่มต้น): REPO_SNAPSHOT.txt

หมายเหตุ

- ทุกไฟล์ถูกเพิ่มภายใต้เส้นทางที่อนุญาต (.github/, docs/, root docs)
- กรุณาตรวจสอบ `CODEOWNERS` เพื่อแก้ไขตัวระบุผู้ดูแลเป็น handle จริงก่อนบันทึกเป็น policy ถาวร

