# Tutorial 1: Your First AI Chat

> **Level:** Beginner | **Time:** 5 minutes
> **Repository:** https://github.com/Alqudimi/PolyAI

---

## Goals

By the end of this tutorial, you will:
- Have PolyAI installed and working
- Send your first chat message to an AI
- Understand the response object
- Know how to switch providers

---

## Prerequisites

- Python 3.9 or higher installed
- `pip` available

---

## Step 1: Install PolyAI

```bash
pip install polyai
```

Verify the installation:

```bash
python -c "import polyai; print('PolyAI', polyai.__version__, 'installed!')"
```

You should see something like: `PolyAI 1.0.0 installed!`

---

## Step 2: Your First Chat

Create a file called `first_chat.py`:

```python
from polyai import Client

# Create a client — no API key needed for this example
client = Client()

# Send a message
response = client.chat(
    provider="ovhcloud",           # which AI service to use
    model="llama-3.1-8b-instruct", # which model to use
    messages=[
        {"role": "user", "content": "What is Python?"}
    ],
)

# Print the response
print(response.text)
```

Run it:

```bash
python first_chat.py
```

You should see a short explanation of Python.

### What happened?

- `Client()` — created a client that manages connections to AI providers
- `provider="ovhcloud"` — we're using OVHcloud AI Endpoints
- `model="llama-3.1-8b-instruct"` — a specific LLaMA 3.1 8B model
- `messages=[...]` — a list of messages in chat format
- `response.text` — the AI's response as a plain string

---

## Step 3: Explore the Response

The response contains more than just text:

```python
from polyai import Client

client = Client()
response = client.chat(
    provider="ovhcloud",
    model="llama-3.1-8b-instruct",
    messages=[{"role": "user", "content": "What is 2 + 2?"}],
)

print(f"Text: {response.text}")
print(f"Tokens used: {response.usage.total_tokens}")
print(f"Why did it stop: {response.finish_reason}")
print(f"Provider: {response.provider}")
print(f"Model: {response.model}")
```

Output:
```
Text: 2 + 2 equals 4.
Tokens used: 14
Why did it stop: stop
Provider: ovhcloud
Model: llama-3.1-8b-instruct
```

---

## Step 4: Add a System Prompt

A system prompt tells the AI how to behave:

```python
response = client.chat(
    provider="ovhcloud",
    model="llama-3.1-8b-instruct",
    messages=[
        {"role": "user", "content": "How are you?"}
    ],
    system="You are a cheerful assistant who always adds emojis to responses.",
)
print(response.text)
# Something like: "I'm doing great! 😊 Ready to help you! 🚀"
```

---

## Step 5: Try Other Providers

PolyAI works with four providers. The same code works for all of them:

```python
from polyai import Client
from polyai.exceptions import UniversalAIError

client = Client()
question = [{"role": "user", "content": "In one sentence: what is AI?"}]

for provider, model in [
    ("ovhcloud",     "llama-3.1-8b-instruct"),
    ("pollinations", "openai"),
    ("mlvoca",       "tinyllama"),
    ("devtoolbox",   "devtoolbox-ai"),
]:
    try:
        response = client.chat(provider=provider, model=model, messages=question, max_tokens=50)
        print(f"\n{provider}: {response.text}")
    except UniversalAIError as e:
        print(f"\n{provider}: Error — {e}")
```

---

## Step 6: Multi-Turn Conversation

AI chat supports back-and-forth conversation:

```python
from polyai import Client

client = Client()

# Build up a conversation
messages = []

# Turn 1
messages.append({"role": "user", "content": "My name is Alice."})
response = client.chat(provider="ovhcloud", model="llama-3.1-8b-instruct", messages=messages)
messages.append({"role": "assistant", "content": response.text})
print(f"AI: {response.text}")

# Turn 2
messages.append({"role": "user", "content": "What is my name?"})
response = client.chat(provider="ovhcloud", model="llama-3.1-8b-instruct", messages=messages)
print(f"AI: {response.text}")
# The AI remembers: "Your name is Alice!"
```

---

## Expected Results

After completing this tutorial, your `first_chat.py` should successfully:

1. Connect to OVHcloud
2. Receive a text response
3. Show token usage
4. Try multiple providers

---

## Troubleshooting

**`ModuleNotFoundError: No module named 'polyai'`**
→ Run `pip install polyai` and try again

**`ConnectionError`**
→ Check your internet connection

**Very slow responses from mlvoca**
→ This is normal. mlvoca runs on community hardware. Try with `timeout=120.0`:
```python
response = client.chat(..., timeout=120.0)
```

---

## Next Steps

- [Tutorial 2: Streaming](02-streaming.md) — see tokens appear in real-time
- [Tutorial 3: Function Calling](03-function-calling.md) — make the AI call your functions
- [Configuration Guide](../user/configuration.md) — API keys and settings
