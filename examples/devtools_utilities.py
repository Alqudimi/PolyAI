"""
devtools_utilities.py — DevToolbox API: AI tools + developer utilities.

All free, no API key required.
"""

from polyai import Client

client = Client()
devtools = client.with_provider("devtoolbox").devtools


# ── AI-powered tools ──────────────────────────────────────────────────────

print("=== Summarize ===")
long_text = """
Python is a versatile, high-level programming language known for its simplicity and
readability. Created by Guido van Rossum in 1991, Python emphasizes code clarity and
expressiveness. It supports multiple programming paradigms including procedural,
object-oriented, and functional programming. Python has a comprehensive standard library
and a rich ecosystem of third-party packages, making it suitable for web development,
data science, artificial intelligence, automation, and scientific computing.
"""
summary = devtools.summarize(long_text, max_length=100)
print(f"Summary: {summary}")


print("\n=== Translate ===")
translations = {
    "fr": devtools.translate("Good morning! How are you today?", "fr"),
    "es": devtools.translate("Good morning! How are you today?", "es"),
    "de": devtools.translate("Good morning! How are you today?", "de"),
}
for lang, text in translations.items():
    print(f"  {lang}: {text}")


print("\n=== Explain Code ===")
code = """
const fibonacci = (n) => n <= 1 ? n : fibonacci(n - 1) + fibonacci(n - 2);
"""
explanation = devtools.explain_code(code)
print(f"Explanation: {explanation}")


print("\n=== Generate Regex ===")
patterns = [
    "match valid email addresses",
    "match US phone numbers in format (xxx) xxx-xxxx",
    "match IPv4 addresses",
]
for desc in patterns:
    pattern = devtools.generate_regex(desc)
    print(f"  [{desc}] → {pattern}")


# ── Developer utilities ────────────────────────────────────────────────────

print("\n=== Developer Utilities ===")

uuid = devtools.generate_uuid()
print(f"UUID: {uuid}")

pwd = devtools.generate_password(length=20, symbols=True)
print(f"Password: {pwd}")

hash_result = devtools.hash("sha256", "hello world")
print(f"SHA256('hello world'): {hash_result}")

lorem = devtools.lorem_ipsum(paragraphs=1)
print(f"Lorem ipsum (first 100 chars): {lorem[:100]}...")


# ── AI chat via standard interface ────────────────────────────────────────

print("\n=== AI Generate (standard chat interface) ===")
response = client.chat(
    provider="devtoolbox",
    model="devtoolbox-ai",
    messages=[{"role": "user", "content": "Write a one-line Python function to reverse a string."}],
)
print(f"Result: {response.text}")

client.close()
