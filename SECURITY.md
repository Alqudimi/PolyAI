# Security Policy

> **Repository:** https://github.com/Alqudimi/PolyAI

## Supported Versions

| Version | Supported |
|---|---|
| 1.x.x (latest) | ✅ Active |
| < 1.0.0 | ❌ End of life |

Security fixes are backported to the **latest minor version** only.

---

## Reporting a Vulnerability

**Do NOT report security vulnerabilities via public GitHub Issues.**

Please report security vulnerabilities by emailing the maintainer directly:

**Email:** security@github.com/Alqudimi *(replace with actual contact)*

Or use [GitHub's private vulnerability reporting](https://github.com/Alqudimi/PolyAI/security/advisories/new).

### What to Include

Please include as much of the following as possible:

- **Type of vulnerability** (e.g., injection, credential leak, dependency)
- **Affected component** (e.g., `polyai/auth/credentials.py`)
- **PolyAI version(s)** affected
- **Steps to reproduce**
- **Proof of concept** (code or curl commands, redacted if needed)
- **Impact assessment** (what an attacker could achieve)
- **Suggested fix** (optional but welcome)

### Response Timeline

| Action | Timeline |
|---|---|
| Initial acknowledgement | Within 48 hours |
| Severity assessment | Within 5 business days |
| Fix development | Depends on severity (see below) |
| Public disclosure | After fix is released |

### Severity & Fix Timeline

| Severity | CVSS Score | Target Fix Timeline |
|---|---|---|
| Critical | 9.0–10.0 | 24–72 hours |
| High | 7.0–8.9 | 7 days |
| Medium | 4.0–6.9 | 30 days |
| Low | 0.1–3.9 | Next release cycle |

---

## Security Architecture

### Secret Masking

All credential objects in PolyAI override `__repr__` to mask sensitive values:

```python
>>> from polyai.auth.credentials import BearerCredentials
>>> cred = BearerCredentials("sk-super-secret-key")
>>> repr(cred)
"BearerCredentials(token='sk-su...key')"
>>> str(cred)
"BearerCredentials(token='sk-su...key')"
```

This prevents accidental leakage in:
- Python tracebacks
- Log files
- Jupyter notebook output
- Debugging sessions

### API Keys in Environment Variables

PolyAI reads API keys **only** from environment variables or explicit constructor arguments. Keys are never:
- Written to disk
- Logged in plaintext
- Included in error messages
- Sent to any telemetry endpoint

```bash
# Recommended: environment variables
export OVHCLOUD_API_KEY="your-key"
export POLLINATIONS_API_KEY="sk_..."
export DEVTOOLBOX_API_KEY="dtb_..."
```

### HTTP Transport Security

All provider requests use HTTPS exclusively. PolyAI uses `httpx` which:
- Validates TLS certificates by default
- Does **not** disable certificate verification
- Follows redirects conservatively

### No Telemetry

PolyAI does not collect any telemetry, usage statistics, or analytics. All HTTP calls go only to the configured provider endpoints.

### Dependency Minimalism

PolyAI has **one production dependency** (`httpx`). This minimises the attack surface from transitive dependencies.

Production dependencies:
```
httpx>=0.25.0
```

Dev dependencies (not installed in production):
```
pytest, pytest-asyncio, pytest-cov, pytest-mock, respx, ruff, mypy, black, pre-commit
```

---

## Security Scanning in CI

Every push and pull request runs:

| Tool | What it checks |
|---|---|
| `pip-audit` | Known CVEs in dependencies |
| `Bandit` | Python SAST (injection, hardcoded secrets, etc.) |
| `TruffleHog` | Committed secrets in git history |
| `CodeQL` | Deep static analysis |
| `dependency-review` | New vulnerable deps in PRs |
| `gitleaks` (pre-commit) | Secrets before they're committed |

---

## Best Practices for Users

### 1. Use Environment Variables

```bash
# Good ✅
export OVHCLOUD_API_KEY="your-key"
client = Client()

# Avoid ❌
client = Client(ovhcloud_api_key="hardcoded-key")  # may appear in logs/source
```

### 2. Never Commit API Keys

Add to `.gitignore`:
```
.env
.env.*
*.key
secrets.json
```

### 3. Rotate Keys Regularly

If a key is accidentally exposed:
1. **Immediately revoke** the key in the provider dashboard
2. **Generate a new key**
3. **Audit git history** for the leaked key using:
   ```bash
   git log --all --full-history -p | grep "your-leaked-key"
   ```
4. If found in history, consider the repository compromised and notify your team

### 4. Validate Provider Responses

When processing AI-generated content that will be executed, parsed as code, or displayed to users:

```python
import json

response = client.chat(..., json_mode=True)
try:
    data = json.loads(response.text)
    # Validate structure before use
    assert isinstance(data.get("name"), str)
except (json.JSONDecodeError, AssertionError, KeyError) as e:
    raise ValueError(f"Invalid AI response: {e}")
```

### 5. Rate Limit Awareness

Be aware that API keys may be rate-limited. Do not:
- Hardcode API keys in mobile apps or frontend JavaScript
- Share keys across environments (use separate keys for dev/staging/prod)

---

## Known Security Considerations

### mlvoca — Non-Commercial Use
mlvoca's terms prohibit commercial use. Using PolyAI with mlvoca in a commercial product may violate the provider's terms of service.

### Pollinations — Anonymous Access
Anonymous Pollinations requests are logged by the provider. For sensitive workloads, use an authenticated API key.

### AI Output Safety
PolyAI does not implement content filtering or output sanitization. If you display AI-generated content to end users, implement your own safety checks appropriate for your use case.

---

## Disclosure Policy

We follow [Coordinated Vulnerability Disclosure (CVD)](https://en.wikipedia.org/wiki/Coordinated_vulnerability_disclosure):

1. Reporter sends vulnerability to maintainer
2. Maintainer acknowledges within 48 hours
3. Maintainer develops fix privately
4. Fix is released as a patch version
5. CVE is requested if applicable
6. Public disclosure after patch release (typically 7 days)
7. Reporter credited in release notes (unless anonymity requested)

---

## Hall of Fame

We appreciate and credit responsible security reporters. Reports that lead to a fix will be listed here.

*(No reports yet — be the first!)*
