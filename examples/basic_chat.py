"""
basic_chat.py — Minimal example: chat with each provider.

No API keys required — OVHcloud, mlvoca, and DevToolbox work anonymously.
Pollinations also works without a key for basic models.
"""

from polyai import Client

client = Client()

# ── OVHcloud (anonymous free tier) ─────────────────────────────────────────

print("=== OVHcloud ===")
response = client.chat(
    provider="ovhcloud",
    model="llama-3.1-8b-instruct",
    messages=[{"role": "user", "content": "What is the capital of France? One word."}],
    temperature=0.0,
    max_tokens=10,
)
print(f"Response: {response.text}")
print(f"Model: {response.model} | Tokens: {response.usage.total_tokens}")


# ── Pollinations (no key needed for basic models) ─────────────────────────

print("\n=== Pollinations ===")
response = client.chat(
    provider="pollinations",
    model="openai",
    messages=[{"role": "user", "content": "Say 'hello world' exactly."}],
    max_tokens=10,
)
print(f"Response: {response.text}")


# ── mlvoca (always free, no key) ──────────────────────────────────────────

print("\n=== mlvoca ===")
response = client.chat(
    provider="mlvoca",
    model="tinyllama",
    messages=[{"role": "user", "content": "What is 2 + 2?"}],
)
print(f"Response: {response.text}")


# ── DevToolbox (no key needed for free tier) ─────────────────────────────

print("\n=== DevToolbox ===")
response = client.chat(
    provider="devtoolbox",
    model="devtoolbox-ai",
    messages=[{"role": "user", "content": "Write a haiku about programming."}],
)
print(f"Response: {response.text}")

client.close()
