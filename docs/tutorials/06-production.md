# Tutorial 6: Production Deployment

> **Level:** Advanced | **Time:** 30 minutes
> **Repository:** https://github.com/Alqudimi/PolyAI

---

## Goals

- Deploy a PolyAI-powered API with FastAPI
- Handle errors gracefully in production
- Set up monitoring and logging
- Configure Docker deployment
- Implement rate limiting and circuit breakers

---

## Step 1: Project Structure

```
my-ai-api/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI app
│   ├── routes.py         # API endpoints
│   ├── ai_client.py      # PolyAI client wrapper
│   └── models.py         # Pydantic request/response models
├── tests/
│   └── test_routes.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.production
```

---

## Step 2: The AI Client Wrapper

`app/ai_client.py`:

```python
"""Production-grade PolyAI client wrapper."""
from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager

from polyai import AsyncClient, ClientConfig
from polyai.config import ProviderConfig
from polyai.exceptions import (
    AuthenticationError,
    RateLimitError,
    ProviderUnavailableError,
    UniversalAIError,
)
from polyai.types import ChatResponse

logger = logging.getLogger(__name__)

# Provider priority list — first available wins
PROVIDER_CHAIN = [
    ("ovhcloud",     "meta-llama-3_3-70b-instruct"),
    ("pollinations", "openai"),
]


class AIClient:
    """Production AI client with failover, logging, and metrics."""

    def __init__(self) -> None:
        config = ClientConfig(
            timeout=45.0,
            max_retries=3,
            providers={
                "mlvoca": ProviderConfig(timeout=120.0, max_retries=1),
            },
        )
        self._client = AsyncClient(config=config)

    async def chat(
        self,
        messages: list[dict],
        *,
        max_tokens: int = 500,
        temperature: float = 0.7,
        request_id: str | None = None,
    ) -> str:
        """Chat with automatic failover. Returns text response."""
        last_error: Exception | None = None

        for provider, model in PROVIDER_CHAIN:
            start = time.monotonic()
            try:
                response: ChatResponse = await self._client.chat(
                    provider=provider,
                    model=model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
                elapsed = time.monotonic() - start
                logger.info(
                    "ai_request_ok",
                    extra={
                        "request_id": request_id,
                        "provider": provider,
                        "model": model,
                        "tokens": response.usage.total_tokens,
                        "latency_ms": int(elapsed * 1000),
                    },
                )
                return response.text

            except AuthenticationError:
                logger.error("ai_auth_error", extra={"provider": provider})
                raise  # don't failover for auth errors

            except RateLimitError as e:
                logger.warning("ai_rate_limited", extra={"provider": provider, "retry_after": e.retry_after})
                last_error = e
                continue  # try next provider

            except ProviderUnavailableError as e:
                logger.warning("ai_provider_down", extra={"provider": provider})
                last_error = e
                continue  # try next provider

            except UniversalAIError as e:
                elapsed = time.monotonic() - start
                logger.error(
                    "ai_request_error",
                    extra={"provider": provider, "error": str(e), "latency_ms": int(elapsed * 1000)},
                )
                last_error = e
                continue

        raise last_error or RuntimeError("All providers failed")

    async def aclose(self) -> None:
        await self._client.aclose()
```

---

## Step 3: FastAPI Application

`app/main.py`:

```python
"""FastAPI application entry point."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.ai_client import AIClient
from app.routes import router

# Shared AI client instance
ai_client: AIClient | None = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    global ai_client
    ai_client = AIClient()
    yield
    await ai_client.aclose()

app = FastAPI(
    title="My AI API",
    description="Powered by PolyAI",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

@app.get("/healthz")
async def health():
    return {"status": "ok", "polyai": True}
```

`app/routes.py`:

```python
"""API routes."""
import uuid
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from polyai.exceptions import UniversalAIError, AuthenticationError
from app.main import ai_client

router = APIRouter(prefix="/api/v1")


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000)
    max_tokens: int = Field(500, ge=1, le=4000)
    temperature: float = Field(0.7, ge=0.0, le=2.0)


class ChatResponse(BaseModel):
    text: str
    request_id: str


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, request: Request):
    request_id = str(uuid.uuid4())
    messages = [{"role": "user", "content": req.message}]

    try:
        text = await ai_client.chat(
            messages=messages,
            max_tokens=req.max_tokens,
            temperature=req.temperature,
            request_id=request_id,
        )
        return ChatResponse(text=text, request_id=request_id)

    except AuthenticationError:
        raise HTTPException(status_code=500, detail="AI service configuration error")
    except UniversalAIError as e:
        raise HTTPException(status_code=502, detail=f"AI service unavailable: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")
```

---

## Step 4: Docker

`Dockerfile`:

```dockerfile
FROM python:3.11-slim

# Security: non-root user
RUN useradd --create-home --shell /bin/bash app
USER app
WORKDIR /home/app

# Install dependencies
COPY --chown=app requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY --chown=app app/ ./app/

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD python -c "import httpx; httpx.get('http://localhost:8000/healthz').raise_for_status()"

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

`docker-compose.yml`:

```yaml
version: "3.9"
services:
  api:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env.production
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/healthz"]
      interval: 30s
      timeout: 10s
      retries: 3
```

`.env.production`:

```bash
OVHCLOUD_API_KEY=your-production-key
POLLINATIONS_API_KEY=sk_...
UNIVERSAL_AI_TIMEOUT=45
UNIVERSAL_AI_MAX_RETRIES=3
```

---

## Step 5: Run It

```bash
# Development
uvicorn app.main:app --reload

# Production (Docker)
docker-compose up -d

# Test it
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is Python?"}'
```

---

## Step 6: Monitoring

Add Prometheus metrics:

```bash
pip install prometheus-fastapi-instrumentator
```

```python
# In main.py
from prometheus_fastapi_instrumentator import Instrumentator

Instrumentator().instrument(app).expose(app)
# Metrics available at /metrics
```

Track AI-specific metrics:

```python
from prometheus_client import Counter, Histogram

ai_requests_total = Counter("ai_requests_total", "Total AI requests", ["provider", "status"])
ai_latency_seconds = Histogram("ai_latency_seconds", "AI request latency", ["provider"])
```

---

## Production Checklist

- [ ] API keys loaded from environment variables
- [ ] `AsyncClient` created once at startup (not per-request)
- [ ] Context manager used for proper cleanup
- [ ] Provider failover implemented
- [ ] Request IDs for tracing
- [ ] Structured logging
- [ ] Health check endpoint (`/healthz`)
- [ ] Error responses don't leak internal details
- [ ] Docker image runs as non-root user
- [ ] CORS configured appropriately
- [ ] Rate limiting on your API (not just AI providers)
- [ ] Monitoring/alerting set up
