"""
Example: Provider Routing & Capability-Based Failover

Demonstrates:
- Routing requests to providers based on capabilities
- Automatic failover when a provider fails
- Capability registry pattern
- Commercial vs non-commercial filtering

Usage:
    python examples/provider_routing.py

No API key required (uses anonymous free tiers).
"""

from __future__ import annotations

from polyai import Client
from polyai.exceptions import FeatureNotSupportedError, UniversalAIError

client = Client()

# ── Capability registry ─────────────────────────────────────────────────────

PROVIDER_CAPABILITIES = {
    "ovhcloud": {
        "chat": True, "stream": True, "embed": True,
        "images": True, "tts": False, "tools": True, "vision": True,
        "commercial": True,
    },
    "pollinations": {
        "chat": True, "stream": True, "embed": True,
        "images": True, "tts": True, "tools": True, "vision": True,
        "commercial": True,
    },
    "mlvoca": {
        "chat": True, "stream": True, "embed": False,
        "images": False, "tts": False, "tools": False, "vision": False,
        "commercial": False,  # non-commercial only!
    },
    "devtoolbox": {
        "chat": True, "stream": False, "embed": False,
        "images": False, "tts": False, "tools": False, "vision": False,
        "commercial": True,
    },
}

DEFAULT_MODELS = {
    "ovhcloud":     "llama-3.1-8b-instruct",
    "pollinations": "openai",
    "mlvoca":       "tinyllama",
    "devtoolbox":   "devtoolbox-ai",
}

# Priority order: highest quality first
PRIORITY = {"ovhcloud": 0, "pollinations": 1, "devtoolbox": 2, "mlvoca": 3}


def providers_for(
    capability: str,
    require_commercial: bool = False,
) -> list[str]:
    """Return providers that support the given capability, sorted by priority."""
    matching = [
        p for p, caps in PROVIDER_CAPABILITIES.items()
        if caps.get(capability)
        and (not require_commercial or caps.get("commercial"))
    ]
    return sorted(matching, key=lambda p: PRIORITY.get(p, 99))


def smart_chat(
    messages: list[dict],
    *,
    need_tools: bool = False,
    need_vision: bool = False,
    need_streaming: bool = False,
    commercial_only: bool = False,
    max_tokens: int = 150,
) -> str | None:
    """
    Route a chat request to the best available provider.

    Automatically tries each capable provider in priority order
    and falls back if one fails.
    """
    # Choose capability requirement
    if need_tools:
        capability = "tools"
    elif need_vision:
        capability = "vision"
    elif need_streaming:
        capability = "stream"
    else:
        capability = "chat"

    chain = providers_for(capability, require_commercial=commercial_only)
    if not chain:
        print(f"  No providers support '{capability}' with commercial={commercial_only}")
        return None

    print(f"  Routing chain for '{capability}': {chain}")

    for provider in chain:
        model = DEFAULT_MODELS[provider]
        try:
            response = client.chat(
                provider=provider,
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                timeout=30.0,
            )
            print(f"  ✅ {provider}/{model}")
            return response.text
        except FeatureNotSupportedError:
            print(f"  ⚠️  {provider}: feature not supported, skipping")
        except UniversalAIError as e:
            print(f"  ❌ {provider}: {type(e).__name__}, trying next...")

    print("  All providers exhausted.")
    return None


def print_capability_matrix() -> None:
    """Print a capability matrix for all providers."""
    capabilities = ["chat", "stream", "embed", "images", "tts", "tools", "vision"]
    header = f"{'Provider':<14}" + "".join(f"{c:<9}" for c in capabilities) + "Commercial"
    print(header)
    print("-" * len(header))
    for provider, caps in PROVIDER_CAPABILITIES.items():
        row = f"{provider:<14}"
        for cap in capabilities:
            row += ("✅" if caps.get(cap) else "❌").ljust(9)
        row += "✅" if caps.get("commercial") else "❌"
        print(row)


def main() -> None:
    messages = [{"role": "user", "content": "Reply with just the number: 2 + 2 = ?"}]

    print("\n📊 Capability Matrix")
    print("=" * 60)
    print_capability_matrix()

    print("\n\n🔀 Routing Demo")
    print("=" * 60)

    scenarios = [
        ("Any provider (default)",         {},                                           ),
        ("Commercial providers only",       {"commercial_only": True},                   ),
        ("Tools-capable providers",         {"need_tools": True},                        ),
        ("Vision-capable providers",        {"need_vision": True},                        ),
        ("Streaming-capable providers",     {"need_streaming": True},                    ),
    ]

    for label, kwargs in scenarios:
        print(f"\n{label}")
        result = smart_chat(messages, max_tokens=20, **kwargs)
        if result:
            print(f"  Answer: {result.strip()}")


if __name__ == "__main__":
    main()
