"""
async_chat.py — Async chat and concurrent multi-provider requests.

Uses AsyncClient for non-blocking I/O — ideal for servers and high-throughput apps.
"""

import asyncio
from polyai import AsyncClient


async def single_chat():
    """Simple async chat."""
    async with AsyncClient() as client:
        response = await client.chat(
            provider="ovhcloud",
            model="llama-3.1-8b-instruct",
            messages=[{"role": "user", "content": "What is Python? One sentence."}],
            max_tokens=60,
        )
        print(f"OVHcloud: {response.text}")


async def async_streaming():
    """Async streaming chat — tokens arrive asynchronously."""
    async with AsyncClient() as client:
        print("Streaming: ", end="", flush=True)
        async for chunk in await client.chat_stream(
            provider="pollinations",
            model="openai",
            messages=[{"role": "user", "content": "Count from 1 to 5."}],
            max_tokens=30,
        ):
            print(chunk.delta, end="", flush=True)
        print()


async def concurrent_requests():
    """Send multiple requests to different providers at the same time."""
    async with AsyncClient() as client:
        responses = await client.chat_many([
            {
                "provider": "ovhcloud",
                "model": "llama-3.1-8b-instruct",
                "messages": [{"role": "user", "content": "Capital of Germany?"}],
                "max_tokens": 10,
            },
            {
                "provider": "pollinations",
                "model": "openai",
                "messages": [{"role": "user", "content": "Capital of Japan?"}],
                "max_tokens": 10,
            },
            {
                "provider": "mlvoca",
                "model": "tinyllama",
                "messages": [{"role": "user", "content": "Capital of France?"}],
            },
        ], max_concurrency=3)

        for i, resp in enumerate(responses):
            print(f"Response {i+1} ({resp.provider}): {resp.text.strip()}")


async def main():
    print("=== Single Chat ===")
    await single_chat()

    print("\n=== Async Streaming ===")
    await async_streaming()

    print("\n=== Concurrent Multi-Provider ===")
    await concurrent_requests()


if __name__ == "__main__":
    asyncio.run(main())
