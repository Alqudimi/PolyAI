# Security Best Practices

> **Repository:** https://github.com/Alqudimi/PolyAI

---

## API Key Management

### Never Hardcode API Keys

```python
# ❌ Bad — key appears in source code
client = Client(ovhcloud_api_key="sk-1234567890abcdef")

# ✅ Good — key from environment variable
import os
client = Client(ovhcloud_api_key=os.environ["OVHCLOUD_API_KEY"])

# ✅ Better — let PolyAI read env vars automatically
client = Client()  # reads OVHCLOUD_API_KEY automatically
```

### Use `.env` Files in Development

```bash
# .env (never commit this)
OVHCLOUD_API_KEY=your-key
POLLINATIONS_API_KEY=sk_...
```

```python
from dotenv import load_dotenv
load_dotenv()
from polyai import Client
client = Client()
```

Add `.env` to `.gitignore`:
```
.env
.env.*
*.key
```

### Rotate Keys Regularly

Best practice: rotate API keys every 90 days. Immediately rotate if:
- A key is accidentally committed to git
- A key appears in logs
- A key is shared with someone who no longer needs access

### Use Separate Keys per Environment

```bash
# Dev key — lower limits, can be rotated more freely
OVHCLOUD_API_KEY_DEV=dev-key

# Staging key — similar limits to production
OVHCLOUD_API_KEY_STAGING=staging-key

# Production key — highest limits, most restricted access
OVHCLOUD_API_KEY_PROD=prod-key
```

---

## Logging Safely

PolyAI masks secrets automatically, but your code must also be careful:

```python
# ❌ Bad — may log raw API key from environment
import logging
logging.debug(f"Config: {os.environ}")

# ❌ Bad — may log response content that contains user PII
logging.debug(f"Response: {response.raw}")

# ✅ Good — log only what you need
logging.info(f"Response received: {response.usage.total_tokens} tokens, "
             f"finish_reason={response.finish_reason}")
```

### Safe Logging Configuration

```python
import logging

# Filter sensitive keys from log records
class SanitisedFormatter(logging.Formatter):
    REDACTED_KEYS = {"api_key", "authorization", "token", "password", "secret"}

    def format(self, record):
        msg = super().format(record)
        for key in self.REDACTED_KEYS:
            # Simple pattern — in production use a proper regex
            if key in msg.lower():
                msg = "[REDACTED LOG ENTRY]"
                break
        return msg
```

---

## Input Validation

### Validate Messages Before Sending

```python
def validate_messages(messages: list[dict]) -> None:
    if not messages:
        raise ValueError("Messages list cannot be empty")

    valid_roles = {"system", "user", "assistant", "tool"}
    for i, msg in enumerate(messages):
        if "role" not in msg:
            raise ValueError(f"Message {i} missing 'role'")
        if msg["role"] not in valid_roles:
            raise ValueError(f"Message {i} has invalid role: {msg['role']}")
        if "content" not in msg and "tool_calls" not in msg:
            raise ValueError(f"Message {i} missing 'content'")

validate_messages(messages)
response = client.chat(...)
```

### Sanitise User Input

When user-provided text is included in prompts, be aware of prompt injection:

```python
# ❌ Risk — user could manipulate the system prompt
user_input = "Ignore previous instructions and..."
messages = [
    {"role": "system", "content": "Be helpful."},
    {"role": "user", "content": user_input},  # could contain injection
]

# ✅ Mitigations:
# 1. Use a separate system message that the model trusts
# 2. Strip or escape XML-like tags from user input
# 3. Use a content moderation step before sending
# 4. Limit user input length

import re

def sanitise_user_input(text: str, max_length: int = 2000) -> str:
    # Truncate
    text = text[:max_length]
    # Remove potential XML/HTML injection
    text = re.sub(r"<[^>]+>", "", text)
    return text.strip()
```

---

## Output Validation

AI-generated output should always be validated before use.

### JSON Output Validation

```python
import json
from jsonschema import validate

response = client.chat(..., json_mode=True)

# Parse
try:
    data = json.loads(response.text)
except json.JSONDecodeError as e:
    raise ValueError(f"AI returned invalid JSON: {e}")

# Validate schema
schema = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "age": {"type": "integer", "minimum": 0, "maximum": 150},
    },
    "required": ["name", "age"],
    "additionalProperties": False,
}

try:
    validate(instance=data, schema=schema)
except Exception as e:
    raise ValueError(f"AI output schema mismatch: {e}")
```

### Code Execution Safety

**Never execute AI-generated code without sandboxing:**

```python
# ❌ Extremely dangerous
exec(response.text)

# ❌ Also dangerous
import subprocess
subprocess.run(response.text, shell=True)

# ✅ If you must execute AI code, use a sandbox:
# - Docker container with no network, no filesystem access
# - RestrictedPython library
# - WebAssembly runtime (e.g., wasmtime)
```

---

## Network Security

### TLS Verification

PolyAI never disables TLS verification. **Do not disable it in your own code:**

```python
# ❌ Never do this
import httpx
httpx.get("https://api.example.com", verify=False)
```

### Proxy Configuration

If your organisation uses a corporate proxy:

```bash
# Set proxy via environment variables (httpx respects these)
export HTTPS_PROXY=http://proxy.company.com:8080
export HTTP_PROXY=http://proxy.company.com:8080
export NO_PROXY=localhost,127.0.0.1
```

---

## Content Safety

### Implement Content Moderation

For user-facing applications, filter both inputs and outputs:

```python
# Simple blocklist example
BLOCKED_PATTERNS = [...]

def is_safe_content(text: str) -> bool:
    text_lower = text.lower()
    return not any(pattern in text_lower for pattern in BLOCKED_PATTERNS)

# Or use a moderation service:
# - OpenAI Moderation API
# - Azure Content Safety
# - AWS Comprehend
```

---

## Deployment Security

### Secret Management in Production

| Platform | Recommended Approach |
|---|---|
| AWS | AWS Secrets Manager or Parameter Store |
| GCP | Secret Manager |
| Azure | Key Vault |
| Kubernetes | Secrets (base64-encoded, plus consider Vault or Sealed Secrets) |
| Docker | `--env-file` or Docker Secrets (Swarm) |
| CI/CD | GitHub Secrets, GitLab CI variables |

### Principle of Least Privilege

Use API keys with the minimum required permissions:
- OVHcloud: Only grant access to needed AI endpoints
- Don't share keys between applications
- Use read-only keys where write access isn't needed

---

## Security Scanning

Run regularly:

```bash
# Check for vulnerable dependencies
pip-audit

# SAST scan
bandit -r polyai/

# Check for committed secrets in history
trufflehog git file:///path/to/repo

# Check .env not in git history
git log --oneline --all -- "*.env" ".env*"
```

See [SECURITY.md](../../SECURITY.md) for reporting vulnerabilities.
