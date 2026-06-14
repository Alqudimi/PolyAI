<div align="center">

# PolyAI

**حزمة Python موحّدة للوصول إلى مزودي الذكاء الاصطناعي المتعددة.**

*واجهة واحدة. أربعة مزودين. بدون تنازلات.*

[![CI](https://github.com/Alqudimi/PolyAI/actions/workflows/ci.yml/badge.svg)](https://github.com/Alqudimi/PolyAI/actions/workflows/ci.yml)
[![PyPI](https://badge.fury.io/py/polyai.svg)](https://badge.fury.io/py/polyai)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

*اقرأ بلغات أخرى: [English](README.md) · [Español](README_ES.md) · [Français](README_FR.md) · [Deutsch](README_DE.md) · [中文](README_ZH.md)*

</div>

---

## ما هي PolyAI؟

**PolyAI** هي حزمة Python احترافية توفر واجهة موحّدة للتفاعل مع أربعة مزودي ذكاء اصطناعي في وقتٍ واحد. بدلاً من تعلّم أربع واجهات برمجية مختلفة، تتعلم واحدة فقط.

---

## التثبيت

```bash
pip install polyai
```

**المتطلبات:** Python 3.9+ · لا مفاتيح API إلزامية

---

## البدء السريع

```python
from polyai import Client

client = Client()

response = client.chat(
    provider="ovhcloud",
    model="llama-3.1-8b-instruct",
    messages=[{"role": "user", "content": "ما هي عاصمة فرنسا؟"}],
)
print(response.text)  # باريس
```

---

## المزودون المدعومون

| المزوّد | الطبقة المجانية | المصادقة | المميزات |
|---|:---:|:---:|---|
| **OVHcloud AI Endpoints** | ✅ مجهول (2 طلب/دقيقة) | اختياري | 40+ نموذج، مستضاف في أوروبا |
| **Pollinations.AI** | ✅ بدون تسجيل | اختياري | توليد صور وصوت، 20+ نموذج |
| **mlvoca** | ✅ مجاني دائماً | ❌ لا يوجد | غير تجاري، متوافق مع Ollama |
| **DevToolbox API** | ✅ 100 ألف طلب/يوم | اختياري | أدوات ذكاء اصطناعي |

---

## الاستخدام المتقدم

### البث المباشر للرموز

```python
for chunk in client.chat_stream(
    provider="pollinations",
    model="openai",
    messages=[{"role": "user", "content": "احكِ لي قصة."}],
):
    print(chunk.delta, end="", flush=True)
```

### الاستخدام غير المتزامن

```python
import asyncio
from polyai import AsyncClient

async def main():
    async with AsyncClient() as client:
        response = await client.chat(
            provider="ovhcloud",
            model="meta-llama-3_3-70b-instruct",
            messages=[{"role": "user", "content": "مرحباً!"}],
        )
        print(response.text)

asyncio.run(main())
```

### توليد الصور

```python
img = client.generate_image(
    provider="pollinations",
    prompt="مدينة مستقبلية ليلاً، فن رقمي",
    model="flux",
    width=1024,
    height=1024,
)
img.images[0].save("output.png")
```

### التضمينات الدلالية

```python
result = client.embed(
    provider="ovhcloud",
    input=["مرحباً بالعالم", "Hello world"],
    model="bge-m3",
)
sim = result.embeddings[0].cosine_similarity(result.embeddings[1])
print(f"التشابه: {sim:.4f}")
```

### معالجة الأخطاء

```python
from polyai.exceptions import RateLimitError, UniversalAIError

try:
    response = client.chat(...)
except RateLimitError as e:
    print(f"تم تجاوز حد الطلبات. أعد المحاولة بعد {e.retry_after} ثانية.")
except UniversalAIError as e:
    print(f"خطأ ({e.provider}، HTTP {e.status_code}): {e}")
```

---

## متغيرات البيئة

```bash
export OVHCLOUD_API_KEY="مفتاحك-هنا"
export POLLINATIONS_API_KEY="sk_..."
export DEVTOOLBOX_API_KEY="dtb_..."
```

---

## التطوير والمساهمة

```bash
git clone https://github.com/Alqudimi/PolyAI.git
cd PolyAI
pip install -e ".[dev]"
pytest tests/unit -v
```

---

## الترخيص

[MIT](LICENSE) — حقوق الملكية © 2026 [عبدالعزيز القديمي](https://github.com/Alqudimi)

---

<div align="center">

صُنع بـ ❤️ بواسطة [عبدالعزيز القديمي](https://github.com/Alqudimi)

⭐ **أعطِ نجمة للمستودع إذا أفادك PolyAI!**

</div>
