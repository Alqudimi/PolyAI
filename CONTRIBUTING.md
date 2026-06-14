# Contributing to PolyAI

> **Repository:** https://github.com/Alqudimi/PolyAI
> **Maintainer:** Abdulaziz Alqudimi

Thank you for your interest in contributing to PolyAI! This document explains how to contribute effectively.

---

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Ways to Contribute](#ways-to-contribute)
- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing Requirements](#testing-requirements)
- [Adding a New Provider](#adding-a-new-provider)
- [Pull Request Process](#pull-request-process)
- [Commit Message Format](#commit-message-format)
- [Release Process](#release-process)

---

## Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md). Please read it before contributing.

---

## Ways to Contribute

### 🐛 Bug Reports

Before opening a bug report:
1. Check [existing issues](https://github.com/Alqudimi/PolyAI/issues)
2. Try the latest version of PolyAI
3. Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

Use the [bug report template](https://github.com/Alqudimi/PolyAI/issues/new?template=bug_report.yml).

### 💡 Feature Requests

Use the [feature request template](https://github.com/Alqudimi/PolyAI/issues/new?template=feature_request.yml). Include:
- What problem does it solve?
- What should the API look like?
- Is it a breaking change?

### 🔌 New Providers

New provider integrations are highly welcome. See [Adding a New Provider](#adding-a-new-provider).

### 📖 Documentation

Documentation improvements (fixes, examples, translations) are always appreciated. Even small fixes matter.

### 🧪 Tests

Additional test cases, especially for edge cases or provider-specific behavior, are very valuable.

---

## Development Setup

### Prerequisites

- Python 3.9 or higher
- Git
- A GitHub account

### Clone and Install

```bash
# Fork the repository first, then:
git clone https://github.com/YOUR_USERNAME/PolyAI.git
cd PolyAI

# Install in editable mode with dev dependencies
pip install -e ".[dev]"

# Verify installation
pytest tests/unit -q
# Expected: 138 passed
```

### Install Pre-commit Hooks

```bash
pip install pre-commit
pre-commit install
pre-commit install --hook-type commit-msg
```

This will:
- Run Ruff linter on every commit
- Check for secrets (gitleaks)
- Validate commit message format

### Verify Your Setup

```bash
# Run linter
ruff check polyai tests

# Run formatter check
ruff format --check polyai tests

# Run type checker
mypy polyai --ignore-missing-imports

# Run tests
pytest tests/unit -v

# All should pass before you start
```

---

## Project Structure

```
PolyAI/
├── polyai/                    # Main SDK package
│   ├── __init__.py            # Public API surface
│   ├── _version.py            # Version string
│   ├── client.py              # Client (sync)
│   ├── async_client.py        # AsyncClient
│   ├── config.py              # ClientConfig, ProviderConfig
│   ├── exceptions.py          # Exception hierarchy
│   ├── auth/
│   │   └── credentials.py     # BearerCredentials, ApiKeyHeaderCredentials, NoAuthCredentials
│   ├── http/
│   │   ├── transport.py       # SyncTransport
│   │   ├── async_transport.py # AsyncTransport
│   │   └── retry.py           # RetryPolicy
│   ├── providers/
│   │   ├── base.py            # BaseProvider (abstract)
│   │   ├── ovhcloud.py        # OVHcloud adapter
│   │   ├── pollinations.py    # Pollinations adapter
│   │   ├── mlvoca.py          # mlvoca adapter
│   │   └── devtoolbox.py      # DevToolbox adapter
│   ├── resources/
│   │   ├── chat.py            # ChatResource, AsyncChatResource
│   │   ├── images.py          # ImagesResource, AsyncImagesResource
│   │   ├── audio.py           # AudioResource, AsyncAudioResource
│   │   ├── embeddings.py      # EmbeddingsResource, AsyncEmbeddingsResource
│   │   ├── devtools.py        # DevToolsResource, AsyncDevToolsResource
│   │   └── models.py          # ModelsResource, AsyncModelsResource
│   ├── streaming/
│   │   └── engine.py          # StreamAccumulator, AsyncStreamAccumulator
│   ├── types/
│   │   ├── chat.py            # ChatResponse, ChatChunk, etc.
│   │   ├── embeddings.py      # EmbeddingResponse, Embedding
│   │   ├── images.py          # ImageResponse, ImageData
│   │   ├── audio.py           # AudioResponse, AudioTranscription
│   │   └── common.py          # Usage, Tool, ToolCall, FunctionDefinition
│   └── utils/
│       └── helpers.py         # build_vision_message, cosine_similarity, etc.
├── tests/
│   ├── unit/                  # Offline tests (mocked HTTP)
│   ├── integration/           # Live provider tests
│   ├── mocks/                 # Shared mock responses
│   └── conftest.py            # Fixtures
├── examples/                  # Runnable examples
├── docs/                      # Documentation
├── pyproject.toml             # Build config, linter config
├── CHANGELOG.md
└── README.md
```

---

## Development Workflow

### 1. Create a Branch

```bash
git checkout -b feat/my-feature     # new feature
git checkout -b fix/bug-description  # bug fix
git checkout -b docs/improve-readme  # documentation
git checkout -b ci/add-workflow      # CI/CD changes
```

Branch naming convention: `type/short-description`

### 2. Make Your Changes

- Keep changes focused — one feature or fix per PR
- Write tests alongside your code
- Update type annotations
- Add docstrings to public functions

### 3. Run Checks Locally

```bash
# All of these must pass before pushing
ruff check polyai tests         # lint
ruff format polyai tests        # format
mypy polyai --ignore-missing-imports  # types
pytest tests/unit -v            # tests
```

### 4. Commit

```bash
git add .
git commit -m "feat(providers): add Groq provider"
```

### 5. Push and Open PR

```bash
git push origin feat/my-feature
# Then open a PR on GitHub
```

---

## Coding Standards

### Python Style

- **Formatter:** Ruff (replaces Black) — 100 char line length
- **Linter:** Ruff (replaces flake8/isort/pyupgrade)
- **Type checker:** MyPy strict mode

### Type Annotations

All public functions must have complete type annotations:

```python
# Good ✅
def embed(
    self,
    provider: str,
    input: str | list[str],
    model: str,
    timeout: float | None = None,
) -> EmbeddingResponse:
    ...

# Bad ❌ — missing annotations
def embed(self, provider, input, model):
    ...
```

### Docstrings

All public classes and methods must have docstrings:

```python
def chat(
    self,
    provider: str,
    model: str,
    messages: list[dict[str, Any]],
    **kwargs: Any,
) -> ChatResponse:
    """Send a chat completion request to the specified provider.

    Args:
        provider: Provider name ("ovhcloud", "pollinations", "mlvoca", "devtoolbox").
        model: Model ID specific to the provider.
        messages: List of message dicts with "role" and "content" keys.
        **kwargs: Additional parameters forwarded to the provider.

    Returns:
        ChatResponse with .text, .usage, .finish_reason, .tool_calls.

    Raises:
        ProviderNotSupportedError: If provider name is unknown.
        AuthenticationError: If the API key is invalid or missing.
        RateLimitError: If the provider rate limit is exceeded.
        UniversalAIError: For any other provider error.

    Example:
        >>> client = Client()
        >>> resp = client.chat(
        ...     provider="ovhcloud",
        ...     model="llama-3.1-8b-instruct",
        ...     messages=[{"role": "user", "content": "Hello!"}],
        ... )
        >>> print(resp.text)
    """
```

### Error Handling

Raise PolyAI exceptions, not raw `Exception`:

```python
# Good ✅
from polyai.exceptions import FeatureNotSupportedError
raise FeatureNotSupportedError("embeddings", provider="mlvoca")

# Bad ❌
raise Exception("mlvoca doesn't support embeddings")
```

### Secret Safety

Never log or repr API keys in plaintext. Use the credential classes:

```python
# Good ✅
from polyai.auth.credentials import BearerCredentials
creds = BearerCredentials(api_key)  # masked in repr

# Bad ❌
print(f"Using key: {api_key}")
```

---

## Testing Requirements

### Unit Tests

All new features must have unit tests. Tests must:

1. **Run offline** — mock all HTTP calls
2. **Cover the happy path** — basic feature works
3. **Cover error paths** — 401, 429, 500, timeout
4. **Be deterministic** — no random seeds, no network calls

```python
# Example unit test structure
class TestMyFeature:
    @pytest.fixture
    def provider(self):
        config = ClientConfig(max_retries=0)
        return MyProvider(config)

    def test_basic_case(self, provider):
        with patch.object(provider._transport, "post") as mock_post:
            mock_post.return_value = {"result": "ok"}
            response = provider.my_method("input")
            assert response.text == "ok"

    def test_auth_error(self, provider):
        with patch.object(provider._transport, "post") as mock_post:
            mock_post.side_effect = AuthenticationError("401", provider="myprovider")
            with pytest.raises(AuthenticationError):
                provider.my_method("input")
```

### Running Tests

```bash
# Unit tests (required — must all pass)
pytest tests/unit -v

# With coverage (target: >90%)
pytest tests/unit --cov=polyai --cov-report=term-missing

# Specific test file
pytest tests/unit/test_providers.py -v

# Specific test
pytest tests/unit/test_providers.py::TestOVHcloudProvider::test_chat -v
```

### Integration Tests

Integration tests are optional but encouraged for new providers:

```bash
UNIVERSAL_AI_INTEGRATION_TESTS=1 pytest tests/integration/test_myprovider.py -v
```

---

## Adding a New Provider

See [docs/dev/adding-providers.md](docs/dev/adding-providers.md) for the complete guide. Summary:

1. Create `polyai/providers/myprovider.py` implementing `BaseProvider`
2. Register in `polyai/providers/__init__.py`
3. Add integration tests in `tests/integration/test_myprovider.py`
4. Add unit tests in `tests/unit/test_providers.py`
5. Add to the capability matrix in `FEATURES.md`
6. Update `CHANGELOG.md`

---

## Pull Request Process

### Before Opening a PR

- [ ] `pytest tests/unit -v` — all tests pass
- [ ] `ruff check polyai tests` — no lint errors
- [ ] `mypy polyai` — no type errors
- [ ] New features have tests
- [ ] `CHANGELOG.md` updated under `[Unreleased]`
- [ ] No secrets or API keys in the code

### PR Title Format

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(providers): add Groq provider
fix(retry): handle Retry-After header with milliseconds
docs(readme): add vision example
ci(release): fix OIDC trusted publishing config
test(ovhcloud): add streaming error test
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`

### Review Process

1. Automated CI must pass (lint, tests, type check, security)
2. At least one maintainer review
3. All review comments resolved
4. No unresolved conflicts with `main`

### Merge Strategy

- **Squash merge** for feature branches (keeps history clean)
- **Merge commit** for release branches

---

## Commit Message Format

```
<type>(<scope>): <subject>

[optional body]

[optional footer]
```

**Examples:**

```
feat(providers): add Groq provider with chat + streaming support

Implements BaseProvider for Groq's OpenAI-compatible API.
Supports chat completions, streaming, and function calling.
Groq does not support embeddings or image generation.

Closes #42
```

```
fix(retry): cap Retry-After at max_wait_seconds

Previously, a very large Retry-After header value could cause
waits of hours. Now capped at RetryPolicy.max_wait_seconds.

Fixes #38
```

---

## First Contribution?

Look for issues labelled [`good first issue`](https://github.com/Alqudimi/PolyAI/labels/good%20first%20issue). These are small, self-contained tasks ideal for first-time contributors.

Join the discussion in [GitHub Discussions](https://github.com/Alqudimi/PolyAI/discussions) if you have questions.

---

## Questions?

- Open a [GitHub Discussion](https://github.com/Alqudimi/PolyAI/discussions)
- Use the [question issue template](https://github.com/Alqudimi/PolyAI/issues/new?template=question.yml)

Thank you for contributing to PolyAI! 🚀
