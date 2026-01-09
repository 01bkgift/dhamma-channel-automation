# TTS Quality Testing Guide

เอกสารสำหรับทดสอบและเปรียบเทียบคุณภาพ TTS providers

## Providers ที่รองรับ

| Provider | Thai Quality | Price | Free Tier | Recommended |
|----------|--------------|-------|-----------|-------------|
| **Google Neural2** | ⭐⭐⭐⭐⭐ | $16/1M chars | 1M chars/month | ✅ **Default** |
| **Google Chirp3-HD** | ⭐⭐⭐⭐ | $16/1M chars | 1M chars/month | ⚠️ ต้องประโยคสั้น |
| **ElevenLabs** | ⭐⭐⭐⭐⭐ | $0.30/video | 10K chars/month | 💰 Premium option |
| **OpenAI TTS** | ⭐⭐ | $15/1M chars | ❌ | ❌ เสียงไทยไม่ชัด |

## วิธีทดสอบ

### 1. Google Neural2 (Default)

```bash
python scripts/tts_generator_google.py \
  --script "test_short_script.txt" \
  --output "audio/test_neural2.mp3" \
  --voice th-TH-Neural2-C \
  --rate 1.0
```

### 2. Google Chirp3-HD

```bash
python scripts/tts_generator_google.py \
  --script "test_short_script.txt" \
  --output "audio/test_chirp3.mp3" \
  --voice th-TH-Chirp3-HD-Schedar \
  --rate 0.80
```

### 3. ElevenLabs (ถ้ามี API key)

```bash
# ต้องติดตั้ง: pip install elevenlabs
python scripts/tts_elevenlabs.py \
  --script "test_short_script.txt" \
  --output "audio/test_elevenlabs.mp3" \
  --voice "Thai Female"
```

## เกณฑ์การประเมินคุณภาพ

1. **ความชัดเจน** - ออกเสียงพยัญชนะ สระ วรรณยุกต์ถูกต้อง
2. **ความเป็นธรรมชาติ** - เสียงไม่ติดๆ ขัดๆ
3. **จังหวะ** - มีจังหวะหยุดเว้นวรรคเหมาะสม
4. **อารมณ์** - เหมาะกับเนื้อหาธรรมะ (สงบ อบอุ่น)

## สรุปคำแนะนำ

- **Production**: ใช้ Google Neural2-C (ฟรี 1M chars/เดือน)
- **Premium**: ใช้ ElevenLabs (คุณภาพสูงสุด แต่มีค่าใช้จ่าย)
- **อย่าใช้**: OpenAI TTS สำหรับภาษาไทย (เสียงไม่ชัด)
