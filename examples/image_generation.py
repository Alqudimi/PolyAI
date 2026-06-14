"""
image_generation.py — Generate images with Pollinations.AI and OVHcloud.

Pollinations offers the most extensive free image generation.
"""

from polyai import Client
from polyai.providers.pollinations import PollinationsProvider

client = Client()


# ── Method 1: URL-based (instant, no API call needed) ─────────────────────

pollinations_provider: PollinationsProvider = client._get_provider("pollinations")  # type: ignore

url = pollinations_provider.generate_image_url(
    "a futuristic city at sunset, digital art, 4k",
    model="flux",
    width=1024,
    height=768,
    seed=42,
    enhance=True,
    nologo=True,
)
print(f"Image URL (no API call): {url}")


# ── Method 2: OpenAI-compatible API endpoint ──────────────────────────────

response = client.generate_image(
    provider="pollinations",
    prompt="a photorealistic mountain lake at dawn, misty atmosphere",
    model="flux",
    width=1024,
    height=1024,
    seed=123,
)
print(f"\nGenerated image URL: {response.url}")
print(f"Total images: {len(response.images)}")

# Save the image locally
if response.images and response.images[0].url:
    print(f"To save: response.images[0].save('output.jpg')")


# ── List available image models ───────────────────────────────────────────

print("\n=== Available Image Models (Pollinations) ===")
from polyai.providers.pollinations import IMAGE_MODELS
for model in IMAGE_MODELS[:10]:
    print(f"  - {model}")
print(f"  (and {len(IMAGE_MODELS) - 10} more...)")


# ── Provider-namespaced API ────────────────────────────────────────────────

pollinations = client.with_provider("pollinations")
img = pollinations.images.generate(
    "a dragon made of code, cyberpunk style",
    model="nanobanana",
    width=512,
    height=512,
)
print(f"\nNanobanana result URL: {img.url}")

client.close()
