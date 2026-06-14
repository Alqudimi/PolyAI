# Installation Guide

> **Repository:** https://github.com/Alqudimi/PolyAI

---

## Requirements

| Requirement | Version |
|---|---|
| Python | 3.9, 3.10, 3.11, or 3.12 |
| pip | 21.0+ recommended |
| Operating System | Linux, macOS, Windows |

No API keys are required for basic usage.

---

## Standard Installation

```bash
pip install polyai
```

Verify:
```bash
python -c "import polyai; print(polyai.__version__)"
```

---

## Installation with Development Extras

For contributing or running tests:

```bash
pip install "polyai[dev]"
```

This installs: `pytest`, `pytest-asyncio`, `pytest-cov`, `pytest-mock`, `respx`, `ruff`, `mypy`, `black`, `pre-commit`

---

## Virtual Environment (Recommended)

Always use a virtual environment to avoid conflicts:

```bash
# Create
python -m venv .venv

# Activate
source .venv/bin/activate   # Linux / macOS
.venv\Scripts\activate      # Windows CMD
.venv\Scripts\Activate.ps1  # Windows PowerShell

# Install
pip install polyai

# Deactivate when done
deactivate
```

---

## Conda

```bash
conda create -n myproject python=3.11
conda activate myproject
pip install polyai
```

---

## Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install PolyAI
RUN pip install --no-cache-dir polyai

COPY . .

CMD ["python", "main.py"]
```

For minimal images using Alpine:
```dockerfile
FROM python:3.11-alpine

RUN pip install --no-cache-dir polyai
```

---

## Installing from Source

For the latest unreleased changes:

```bash
git clone https://github.com/Alqudimi/PolyAI.git
cd PolyAI
pip install -e ".[dev]"
```

---

## Pinning Versions (Production)

For production deployments, pin the exact version:

```txt
# requirements.txt
polyai==1.0.0
```

Or with `pip-compile` (recommended):

```bash
pip install pip-tools
echo "polyai" > requirements.in
pip-compile requirements.in
# Generates requirements.txt with all locked versions
```

---

## Verifying the Installation

```python
# verify_install.py
import polyai
from polyai import Client, AsyncClient
from polyai.exceptions import UniversalAIError
from polyai.types import ChatResponse

print(f"✅ PolyAI {polyai.__version__} installed successfully")
print(f"   Python: {__import__('sys').version.split()[0]}")
print(f"   httpx:  {__import__('httpx').__version__}")
```

---

## Troubleshooting Installation

### `pip: command not found`
```bash
python -m pip install polyai
# or
python3 -m pip install polyai
```

### `ERROR: Could not find a version that satisfies the requirement polyai`
Check Python version — must be 3.9+:
```bash
python --version
```

### SSL errors
```bash
pip install polyai --trusted-host pypi.org --trusted-host files.pythonhosted.org
```

### Permission errors
```bash
pip install --user polyai
# or use a virtual environment (recommended)
```

See [TROUBLESHOOTING.md](../../TROUBLESHOOTING.md) for more.
