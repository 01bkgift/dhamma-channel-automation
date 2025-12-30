# ตัวอย่างสัญญาเมทาดาทาเสียงบรรยาย (TTS)

ไฟล์ `voiceover_v1_example.json` คือสัญญาอ้างอิงของเมทาดาทาเสียงบรรยายเวอร์ชัน 1
เพื่อเป็นแหล่งอ้างอิงหลัก (single source of truth) สำหรับ schema ที่ต้องคงที่

## สิ่งที่อยู่ในโฟลเดอร์นี้

- `input.txt` ข้อความต้นฉบับสำหรับคำนวณค่า `input_sha256`
- `voiceover_v1_example.json` เมทาดาทาอ้างอิงของสัญญาเวอร์ชัน 1

## วิธีสร้างไฟล์เสียง (ถ้าไม่มี WAV ใน repo)

รันคำสั่งนี้จากโฟลเดอร์โปรเจกต์:

```bash
python scripts/tts_generate.py --run-id sample_run --slug voiceover_demo --script samples/reference/tts/input.txt
```

ไฟล์เสียงและเมทาดาทาจะถูกสร้างที่:

```
data/voiceovers/sample_run/
```

หมายเหตุ: ตัวอย่างนี้แสดงเฉพาะฟิลด์ที่บังคับใช้ หากต้องการฟิลด์เสริม
เช่น `voice`, `style` (ผ่าน CLI) หรือ `created_utc` (ผ่านโค้ด) สามารถเพิ่มได้
โดยยังคง backward compatible
