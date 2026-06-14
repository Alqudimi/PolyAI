"""
structured_output.py — Extract structured data using JSON mode.

Demonstrates extracting structured JSON from unstructured text.
"""

import json
from polyai import Client

client = Client()

# ── Extract structured data ───────────────────────────────────────────────

print("=== Entity Extraction ===")
response = client.chat(
    provider="ovhcloud",
    model="meta-llama-3_3-70b-instruct",
    messages=[{
        "role": "user",
        "content": (
            "Extract the following entities from this text as JSON:\n"
            "Text: 'John Smith, aged 32, works as a software engineer at Acme Corp in San Francisco.'\n"
            "Return JSON with keys: name, age, job_title, company, city"
        ),
    }],
    json_mode=True,
    temperature=0.0,
    max_tokens=200,
)

try:
    data = json.loads(response.text)
    print(f"Extracted: {json.dumps(data, indent=2)}")
except json.JSONDecodeError:
    print(f"Raw response: {response.text}")


# ── Sentiment analysis ────────────────────────────────────────────────────

print("\n=== Sentiment Analysis ===")
reviews = [
    "This product is absolutely amazing! Best purchase I've ever made.",
    "Terrible quality, broke after one day. Complete waste of money.",
    "It's okay, nothing special but works as expected.",
]

for review in reviews:
    resp = client.chat(
        provider="ovhcloud",
        model="meta-llama-3_3-70b-instruct",
        messages=[{
            "role": "user",
            "content": (
                f"Analyse the sentiment of this review. "
                f"Return JSON with: sentiment (positive/negative/neutral), "
                f"confidence (0.0-1.0), key_phrases (list of up to 3 strings).\n\n"
                f"Review: {review}"
            ),
        }],
        json_mode=True,
        temperature=0.0,
        max_tokens=150,
    )
    try:
        result = json.loads(resp.text)
        print(f"  Review: \"{review[:50]}...\"")
        print(f"  Sentiment: {result.get('sentiment')} ({result.get('confidence', 0):.0%})")
        print()
    except json.JSONDecodeError:
        print(f"  Raw: {resp.text}")


# ── Classification ────────────────────────────────────────────────────────

print("=== Zero-shot Classification ===")
text = "My laptop screen flickered twice and then went completely black."
categories = ["hardware_issue", "software_bug", "user_error", "network_problem"]

resp = client.chat(
    provider="ovhcloud",
    model="meta-llama-3_3-70b-instruct",
    messages=[{
        "role": "user",
        "content": (
            f"Classify this support ticket into one of these categories: {categories}.\n"
            f"Return JSON with: category (one of the options), confidence (0.0-1.0), reasoning (short).\n\n"
            f"Ticket: {text}"
        ),
    }],
    json_mode=True,
    temperature=0.0,
    max_tokens=150,
)

try:
    result = json.loads(resp.text)
    print(f"Category: {result.get('category')}")
    print(f"Confidence: {result.get('confidence', 0):.0%}")
    print(f"Reasoning: {result.get('reasoning', '')}")
except json.JSONDecodeError:
    print(resp.text)

client.close()
