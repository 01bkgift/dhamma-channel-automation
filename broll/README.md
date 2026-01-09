# B-roll Images Directory

โฟลเดอร์นี้ใช้เก็บภาพประกอบ (B-roll) สำหรับใช้ใน video rendering.

## โครงสร้าง

```
broll/
├── README.md      # ไฟล์นี้
├── dhamma/        # ภาพธรรมะทั่วไป
├── meditation/    # ภาพการทำสมาธิ
├── nature/        # ภาพธรรมชาติสงบ
└── temple/        # ภาพวัดและพระพุทธรูป
```

## ข้อกำหนด

- **Format**: JPG, JPEG, หรือ PNG
- **Resolution**: แนะนำ 1920x1080 (Full HD) หรือสูงกว่า
- **Aspect Ratio**: 16:9
- **License**: ต้องมีสิทธิ์ใช้งาน (public domain, CC0, หรือซื้อลิขสิทธิ์)

## การใช้งาน

Video renderer จะ:
1. ค้นหาภาพในโฟลเดอร์ `broll/` และ subdirectories
2. สลับภาพทุก 7 วินาทีตามความยาวของเสียง
3. ถ้าไม่มีภาพ จะใช้ gradient background แทน

## แหล่งภาพฟรี

- [Unsplash](https://unsplash.com) - ฟรี, ไม่ต้อง attribution
- [Pexels](https://pexels.com) - ฟรี, ไม่ต้อง attribution
- [Pixabay](https://pixabay.com) - ฟรี, ไม่ต้อง attribution
- [DALL-E](https://openai.com/dall-e-3) - สร้างจาก AI (ต้องมี API key)

## หมายเหตุ

> ⚠️ Repository นี้เป็น public - ห้ามเก็บภาพขนาดใหญ่ใน Git
> แนะนำให้ download ภาพไว้ใน local หรือใช้ DALL-E generate ตอน runtime
