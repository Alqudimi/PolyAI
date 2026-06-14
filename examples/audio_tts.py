"""
audio_tts.py — Text-to-speech with Pollinations.AI.

Generates MP3 audio from text using various voices.
Requires a Pollinations API key for TTS access.
"""

import os
from polyai import Client

client = Client(pollinations_api_key=os.getenv("POLLINATIONS_API_KEY", ""))

# ── Basic TTS ──────────────────────────────────────────────────────────────

print("Generating speech...")
audio = client.text_to_speech(
    provider="pollinations",
    text="Hello! This is a demonstration of the polyai SDK's text-to-speech capability.",
    voice="alloy",
    response_format="mp3",
    speed=1.0,
)

audio.save("output_alloy.mp3")
print(f"Saved: output_alloy.mp3 ({len(audio.content):,} bytes)")


# ── Different voice ────────────────────────────────────────────────────────

audio2 = client.text_to_speech(
    provider="pollinations",
    text="The quick brown fox jumps over the lazy dog.",
    voice="nova",
    speed=0.9,
)
audio2.save("output_nova.mp3")
print(f"Saved: output_nova.mp3 ({len(audio2.content):,} bytes)")


# ── Using the namespaced API ───────────────────────────────────────────────

pollinations = client.with_provider("pollinations")
audio3 = pollinations.audio.speech(
    "This demonstrates the namespaced audio resource.",
    voice="echo",
)
audio3.save("output_echo.mp3")
print(f"Saved: output_echo.mp3 ({len(audio3.content):,} bytes)")

client.close()
