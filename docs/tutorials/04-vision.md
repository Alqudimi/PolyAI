# Tutorial 4: Vision (Multimodal)

> **Level:** Intermediate | **Time:** 15 minutes
> **Repository:** https://github.com/Alqudimi/PolyAI

---

## Goals

- Send images alongside text to AI models
- Use URLs, local files, and base64 images
- Compare multiple images
- Build an image analysis pipeline

---

## Prerequisites

- Completed [Tutorial 1](01-first-chat.md)
- PolyAI installed

---

## What is Vision?

Vision-capable (multimodal) AI models can see images. Instead of only processing text, they accept:
- **Image URLs** — linked images from the web
- **Local files** — images on your disk
- **Base64 data** — images encoded as text strings

---

## Step 1: Analyse an Image from URL

```python
from polyai import Client
from polyai.utils import build_vision_message

client = Client()

# Build a message with an image
message = build_vision_message(
    text="What is in this image? Describe it in detail.",
    image="https://upload.wikimedia.org/wikipedia/commons/thumb/4/47/PNG_transparency_demonstration_1.png/280px-PNG_transparency_demonstration_1.png",
)

response = client.chat(
    provider="ovhcloud",
    model="Qwen/Qwen3-VL-8B-Instruct",  # vision model
    messages=[message],
    max_tokens=200,
)

print(response.text)
```

---

## Step 2: Analyse a Local Image

```python
from polyai import Client
from polyai.utils import build_vision_message

client = Client()

# PolyAI automatically loads the file and converts to base64
message = build_vision_message(
    text="What text can you see in this image?",
    image="/path/to/screenshot.png",  # local file path
)

response = client.chat(
    provider="ovhcloud",
    model="Qwen/Qwen3-VL-8B-Instruct",
    messages=[message],
    max_tokens=150,
)
print(response.text)
```

---

## Step 3: Multiple Images

```python
from polyai import Client
from polyai.utils import build_vision_message

client = Client()

# Compare two images
message = build_vision_message(
    text="Compare these two images. What are the differences?",
    image=[
        "https://example.com/image1.jpg",
        "https://example.com/image2.jpg",
    ],
)

response = client.chat(
    provider="ovhcloud",
    model="Qwen/Qwen3-VL-8B-Instruct",
    messages=[message],
    max_tokens=300,
)
print(response.text)
```

---

## Step 4: Image + Conversation Context

Combine vision with multi-turn conversation:

```python
from polyai import Client
from polyai.utils import build_vision_message

client = Client()

# First message: send the image
vision_msg = build_vision_message(
    "I'm looking at this chart.",
    "https://example.com/sales_chart.png",
)

messages = [vision_msg]

# Ask first question
messages.append({"role": "user", "content": "What type of chart is this?"})
response1 = client.chat(
    provider="ovhcloud",
    model="Qwen/Qwen3-VL-8B-Instruct",
    messages=messages,
    max_tokens=100,
)
messages.append({"role": "assistant", "content": response1.text})
print(f"Q1: {response1.text}")

# Ask follow-up (model remembers the image)
messages.append({"role": "user", "content": "What is the highest value shown?"})
response2 = client.chat(
    provider="ovhcloud",
    model="Qwen/Qwen3-VL-8B-Instruct",
    messages=messages,
    max_tokens=100,
)
print(f"Q2: {response2.text}")
```

---

## Step 5: Build an Image Analysis Pipeline

```python
from polyai import Client
from polyai.utils import build_vision_message
from polyai.exceptions import UniversalAIError
import json

client = Client()

def analyse_image(image_url: str) -> dict:
    """Analyse an image and return structured data."""

    system = """You are an image analyser. Always respond with valid JSON containing:
{
  "description": "brief description",
  "objects": ["list", "of", "objects"],
  "colors": ["dominant", "colors"],
  "text_content": "any text visible in the image or null",
  "mood": "overall mood/tone"
}"""

    message = build_vision_message(
        "Analyse this image completely.",
        image_url,
    )

    try:
        response = client.chat(
            provider="ovhcloud",
            model="Qwen/Qwen3-VL-8B-Instruct",
            messages=[message],
            system=system,
            json_mode=True,
            temperature=0.0,
            max_tokens=300,
        )
        return json.loads(response.text)
    except (json.JSONDecodeError, UniversalAIError) as e:
        return {"error": str(e)}


# Test it
result = analyse_image("https://upload.wikimedia.org/wikipedia/commons/a/a7/Camponotus_flavomarginatus_ant.jpg")
print(json.dumps(result, indent=2))
```

---

## Vision Models

| Provider | Model | Notes |
|---|---|---|
| OVHcloud | `Qwen/Qwen3-VL-8B-Instruct` | Best vision quality |
| OVHcloud | `meta-llama/Llama-3.2-11B-Vision-Instruct` | Good alternative |
| Pollinations | `openai` | GPT-4o with vision |

---

## Common Use Cases

| Use Case | Approach |
|---|---|
| Image description | "Describe this image" |
| OCR (text extraction) | "Extract all text visible in this image" |
| Chart reading | "What does this chart show? What are the key values?" |
| Product inspection | "Is there any damage or defect in this image?" |
| Face emotion detection | "What emotions are expressed in this image?" |
| Diagram understanding | "Explain this architecture diagram" |

---

## Troubleshooting

**`FeatureNotSupportedError`**
→ The model you chose doesn't support vision. Use a vision-capable model like `Qwen/Qwen3-VL-8B-Instruct`.

**Empty response for an image URL**
→ The image URL may be unreachable from the provider's servers. Try hosting the image at a public URL.

**Slow response for large images**
→ Vision models process images as tokens. Very large images take longer. Resize to 1024×1024 or less before sending.

---

## Next Steps

- [Tutorial 5: Embeddings](05-embeddings.md) — semantic search
- [Tutorial 6: Production](06-production.md) — deploy your vision app
