# Production Guide

> **Repository:** https://github.com/Alqudimi/PolyAI

This guide covers deploying PolyAI-based applications to production environments.

---

## Architecture Patterns

### Pattern 1: Simple Script / CLI

```python
# main.py
import os
from polyai import Client

def main():
    client = Client()
    response = client.chat(
        provider="ovhcloud",
        model="llama-3.1-8b-instruct",
        messages=[{"role": "user", "content": "Hello!"}],
    )
    print(response.text)
    client.close()

if __name__ == "__main__":
    main()
```

### Pattern 2: FastAPI Web Service

```python
# app.py
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from polyai import AsyncClient
from polyai.exceptions import UniversalAIError

# Shared client — created once at startup
polyai_client: AsyncClient | None = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global polyai_client
    polyai_client = AsyncClient()
    yield
    await polyai_client.aclose()

app = FastAPI(lifespan=lifespan)

class ChatRequest(BaseModel):
    message: str
    provider: str = "ovhcloud"

@app.post("/chat")
async def chat(req: ChatRequest):
    try:
        response = await polyai_client.chat(
            provider=req.provider,
            model="llama-3.1-8b-instruct",
            messages=[{"role": "user", "content": req.message}],
            max_tokens=500,
            timeout=30.0,
        )
        return {"text": response.text, "tokens": response.usage.total_tokens}
    except UniversalAIError as e:
        raise HTTPException(status_code=502, detail=str(e))
```

### Pattern 3: Django View

```python
# views.py
from django.http import JsonResponse
from django.views import View
from polyai import Client
from polyai.exceptions import UniversalAIError

# Module-level client — Django is multi-threaded, SyncTransport is thread-safe
_client = Client()

class ChatView(View):
    def post(self, request):
        import json
        data = json.loads(request.body)
        try:
            response = _client.chat(
                provider="ovhcloud",
                model="llama-3.1-8b-instruct",
                messages=[{"role": "user", "content": data["message"]}],
                max_tokens=500,
            )
            return JsonResponse({"text": response.text})
        except UniversalAIError as e:
            return JsonResponse({"error": str(e)}, status=502)
```

### Pattern 4: Celery Background Task

```python
# tasks.py
from celery import Celery
from polyai import Client
from polyai.exceptions import UniversalAIError

app = Celery("tasks")

# Client per worker process (Celery workers are separate processes)
_client = None

def get_client():
    global _client
    if _client is None:
        _client = Client()
    return _client

@app.task(bind=True, max_retries=3)
def process_ai_request(self, message: str):
    try:
        response = get_client().chat(
            provider="ovhcloud",
            model="llama-3.1-8b-instruct",
            messages=[{"role": "user", "content": message}],
        )
        return response.text
    except UniversalAIError as exc:
        raise self.retry(exc=exc, countdown=60)
```

---

## Docker Deployment

### Dockerfile

```dockerfile
FROM python:3.11-slim

# Security: don't run as root
RUN useradd --create-home appuser
USER appuser
WORKDIR /home/appuser/app

# Install dependencies first (better layer caching)
COPY --chown=appuser requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY --chown=appuser . .

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD python -c "import polyai; print('ok')" || exit 1

CMD ["python", "main.py"]
```

### docker-compose.yml

```yaml
version: "3.9"
services:
  app:
    build: .
    environment:
      - OVHCLOUD_API_KEY=${OVHCLOUD_API_KEY}
      - POLLINATIONS_API_KEY=${POLLINATIONS_API_KEY}
      - UNIVERSAL_AI_TIMEOUT=60
      - UNIVERSAL_AI_MAX_RETRIES=3
    env_file:
      - .env.production
    restart: unless-stopped
```

---

## Kubernetes Deployment

### deployment.yaml

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: polyai-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: polyai-app
  template:
    metadata:
      labels:
        app: polyai-app
    spec:
      containers:
        - name: app
          image: your-registry/polyai-app:1.0.0
          env:
            - name: OVHCLOUD_API_KEY
              valueFrom:
                secretKeyRef:
                  name: polyai-secrets
                  key: ovhcloud-api-key
            - name: UNIVERSAL_AI_TIMEOUT
              value: "60"
          resources:
            requests:
              memory: "128Mi"
              cpu: "100m"
            limits:
              memory: "512Mi"
              cpu: "500m"
          livenessProbe:
            httpGet:
              path: /healthz
              port: 8000
            initialDelaySeconds: 10
            periodSeconds: 30
```

### secrets.yaml

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: polyai-secrets
type: Opaque
stringData:
  ovhcloud-api-key: "your-key-here"
```

---

## Environment Management

### Separate Keys per Environment

```bash
# .env.development
OVHCLOUD_API_KEY=dev-key-with-low-limits

# .env.staging
OVHCLOUD_API_KEY=staging-key

# .env.production
OVHCLOUD_API_KEY=production-key-with-high-limits
```

### AWS Secrets Manager

```python
import boto3
import json

def get_secret(secret_name: str) -> dict:
    client = boto3.client("secretsmanager")
    response = client.get_secret_value(SecretId=secret_name)
    return json.loads(response["SecretString"])

secrets = get_secret("polyai/production")

from polyai import Client, ClientConfig
polyai_client = Client(config=ClientConfig(
    ovhcloud_api_key=secrets["ovhcloud_api_key"],
    pollinations_api_key=secrets["pollinations_api_key"],
))
```

---

## Observability

### Structured Logging

```python
import logging
import json
from polyai import Client
from polyai.exceptions import UniversalAIError

logger = logging.getLogger(__name__)

def chat_with_logging(messages: list, request_id: str) -> str:
    logger.info(json.dumps({
        "event": "ai_request_start",
        "request_id": request_id,
        "provider": "ovhcloud",
        "message_count": len(messages),
    }))

    try:
        response = client.chat(
            provider="ovhcloud",
            model="llama-3.1-8b-instruct",
            messages=messages,
        )
        logger.info(json.dumps({
            "event": "ai_request_success",
            "request_id": request_id,
            "tokens": response.usage.total_tokens,
            "finish_reason": response.finish_reason,
        }))
        return response.text

    except UniversalAIError as e:
        logger.error(json.dumps({
            "event": "ai_request_error",
            "request_id": request_id,
            "error_type": type(e).__name__,
            "provider": getattr(e, "provider", "unknown"),
            "status_code": getattr(e, "status_code", None),
        }))
        raise
```

### Rate Limit Budget Tracking

```python
from collections import defaultdict
from datetime import datetime, timedelta
import threading

class RateLimitBudget:
    """Track request counts to stay under provider rate limits."""

    def __init__(self, requests_per_minute: int = 2):
        self.limit = requests_per_minute
        self.counts = defaultdict(list)
        self.lock = threading.Lock()

    def can_request(self, provider: str) -> bool:
        with self.lock:
            now = datetime.utcnow()
            cutoff = now - timedelta(minutes=1)
            self.counts[provider] = [t for t in self.counts[provider] if t > cutoff]
            if len(self.counts[provider]) < self.limit:
                self.counts[provider].append(now)
                return True
            return False

budget = RateLimitBudget(requests_per_minute=2)

def rate_limited_chat(messages):
    if not budget.can_request("ovhcloud"):
        raise RuntimeError("Rate limit budget exhausted")
    return client.chat(provider="ovhcloud", model="...", messages=messages)
```

---

## Health Checks

```python
# health.py
from polyai import Client
from polyai.exceptions import UniversalAIError

def health_check() -> dict:
    """Check PolyAI connectivity. Returns status dict."""
    results = {}

    for provider, model in [
        ("ovhcloud",     "llama-3.1-8b-instruct"),
        ("pollinations", "openai"),
    ]:
        try:
            client.chat(
                provider=provider,
                model=model,
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=1,
                timeout=5.0,
            )
            results[provider] = "ok"
        except UniversalAIError as e:
            results[provider] = f"error: {e}"

    return results
```

---

## Performance Tuning

### Connection Pooling

PolyAI reuses HTTP connections automatically. For high-throughput applications:

```python
# AsyncClient maintains a persistent connection pool
# Use it for all requests in async applications
async with AsyncClient() as client:
    # All requests share the connection pool
    tasks = [client.chat(...) for _ in range(100)]
    results = await asyncio.gather(*tasks)
```

### Concurrency Limits

```python
# Limit concurrent requests to avoid overwhelming providers
results = await client.chat_many(
    requests,
    max_concurrency=5,  # adjust based on your rate limit tier
)
```

See [Performance Best Practices](performance.md) for more.
