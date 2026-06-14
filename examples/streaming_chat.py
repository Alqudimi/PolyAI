"""
streaming_chat.py — Real-time token streaming from OVHcloud and Pollinations.

Tokens are printed as they arrive, providing an interactive experience.
"""

from polyai import Client
from polyai.streaming import StreamAccumulator

client = Client()

# ── Sync streaming ─────────────────────────────────────────────────────────

print("=== OVHcloud Streaming ===")
print("Response: ", end="", flush=True)

acc = StreamAccumulator()
for chunk in client.chat_stream(
    provider="ovhcloud",
    model="llama-3.1-8b-instruct",
    messages=[{"role": "user", "content": "Tell me a very short story in exactly 3 sentences."}],
    max_tokens=150,
):
    print(chunk.delta, end="", flush=True)
    acc.add(chunk)

final = acc.result()
print(f"\n\nFinish reason: {final.finish_reason}")


# ── Stream accumulation shortcut ──────────────────────────────────────────

print("\n=== Pollinations Streaming (accumulated) ===")
print("Streaming: ", end="", flush=True)

response = client.chat_accumulate(
    provider="pollinations",
    model="openai",
    messages=[{"role": "user", "content": "What are the three laws of thermodynamics? One sentence each."}],
    max_tokens=200,
    on_chunk=lambda c: print(c.delta, end="", flush=True),
)

print(f"\n\nTotal length: {len(response.text)} chars")

client.close()
