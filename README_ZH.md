<div align="center">

# PolyAI

**面向多个 AI 提供商的生产级 Python SDK。**

*一个接口。四个提供商。零妥协。*

[![CI](https://github.com/Alqudimi/PolyAI/actions/workflows/ci.yml/badge.svg)](https://github.com/Alqudimi/PolyAI/actions/workflows/ci.yml)
[![PyPI](https://badge.fury.io/py/polyai.svg)](https://badge.fury.io/py/polyai)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

*其他语言版本: [English](README.md) · [العربية](README_AR.md) · [Español](README_ES.md) · [Français](README_FR.md) · [Deutsch](README_DE.md)*

</div>

---

## 什么是 PolyAI？

**PolyAI** 是一个生产级 Python SDK，为四个 AI 提供商提供单一统一的接口。无需学习四种不同的 API，只需学习一种。

---

## 安装

```bash
pip install polyai
```

**要求：** Python 3.9+ · 无强制 API 密钥

---

## 快速开始

```python
from polyai import Client

client = Client()

response = client.chat(
    provider="ovhcloud",
    model="llama-3.1-8b-instruct",
    messages=[{"role": "user", "content": "法国的首都是什么？"}],
)
print(response.text)  # 巴黎
```

---

## 支持的提供商

| 提供商 | 免费套餐 | 身份验证 | 亮点 |
|---|:---:|:---:|---|
| **OVHcloud AI Endpoints** | ✅ 匿名（2次/分钟） | 可选 | 40+ 模型，欧盟托管 |
| **Pollinations.AI** | ✅ 无需注册 | 可选 | 图像、TTS、20+ LLMs |
| **mlvoca** | ✅ 始终免费 | ❌ 无 | 非商业，Ollama 兼容 |
| **DevToolbox API** | ✅ 10万次/天 | 可选 | AI 开发者工具 |

---

## 功能特性

### 流式传输

```python
for chunk in client.chat_stream(
    provider="pollinations",
    model="openai",
    messages=[{"role": "user", "content": "给我讲个故事。"}],
):
    print(chunk.delta, end="", flush=True)
```

### 异步使用

```python
import asyncio
from polyai import AsyncClient

async def main():
    async with AsyncClient() as client:
        response = await client.chat(
            provider="ovhcloud",
            model="meta-llama-3_3-70b-instruct",
            messages=[{"role": "user", "content": "你好！"}],
        )
        print(response.text)

asyncio.run(main())
```

### 图像生成

```python
img = client.generate_image(
    provider="pollinations",
    prompt="夜晚的未来城市，数字艺术",
    model="flux",
    width=1024,
    height=1024,
)
img.images[0].save("output.png")
```

### 错误处理

```python
from polyai.exceptions import RateLimitError, UniversalAIError

try:
    response = client.chat(...)
except RateLimitError as e:
    print(f"请求限制。{e.retry_after}秒后重试")
except UniversalAIError as e:
    print(f"错误（{e.provider}，HTTP {e.status_code}）：{e}")
```

---

## 许可证

[MIT](LICENSE) — 版权所有 © 2026 [Abdulaziz Alqudimi](https://github.com/Alqudimi)
