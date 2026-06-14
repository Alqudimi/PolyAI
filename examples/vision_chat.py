"""
vision_chat.py — Multimodal vision chat with OVHcloud Qwen3-VL.

Send an image URL alongside a question and have the model describe it.
"""

from polyai import Client
from polyai.utils import build_vision_message

client = Client()

# Build a multimodal message with image + text
message = build_vision_message(
    "What does this image show? Please describe it in detail.",
    "https://upload.wikimedia.org/wikipedia/commons/thumb/4/47/PNG_transparency_demonstration_1.png/280px-PNG_transparency_demonstration_1.png",
)

response = client.chat(
    provider="ovhcloud",
    model="Qwen/Qwen3-VL-8B-Instruct",
    messages=[message],
    max_tokens=200,
)

print(f"Vision Response:\n{response.text}")
print(f"\nModel: {response.model}")

# ── Multiple images in one message ────────────────────────────────────────

multi_msg = build_vision_message(
    "Compare these two images.",
    [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/4/47/PNG_transparency_demonstration_1.png/280px-PNG_transparency_demonstration_1.png",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a7/Camponotus_flavomarginatus_ant.jpg/640px-Camponotus_flavomarginatus_ant.jpg",
    ],
)

response2 = client.chat(
    provider="ovhcloud",
    model="Qwen/Qwen3-VL-8B-Instruct",
    messages=[multi_msg],
    max_tokens=300,
)
print(f"\nMulti-image Response:\n{response2.text}")

client.close()
