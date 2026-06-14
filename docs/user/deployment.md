# Deployment Guide

> **Repository:** https://github.com/Alqudimi/PolyAI

This guide covers deploying applications built with PolyAI to various environments.

---

## Deployment Checklist

Before deploying:

- [ ] All secrets stored in environment variables (not in code)
- [ ] `Client` or `AsyncClient` created once and reused
- [ ] Appropriate timeout configured for your SLA
- [ ] Error handling implemented (failover, retries)
- [ ] Health check endpoint implemented
- [ ] Logging configured (structured, no secrets)
- [ ] Dependencies pinned in `requirements.txt`

---

## Environment Setup

### Create `requirements.txt`

```bash
pip install polyai
pip freeze | grep polyai >> requirements.txt
# Or pin exactly:
echo "polyai==1.0.0" > requirements.txt
```

### Environment Variables

Required environment variables (set per environment):

```bash
# Production
OVHCLOUD_API_KEY=prod-key
POLLINATIONS_API_KEY=sk_prod_...
DEVTOOLBOX_API_KEY=dtb_prod_...
UNIVERSAL_AI_TIMEOUT=45
UNIVERSAL_AI_MAX_RETRIES=3
```

---

## Docker

### Minimal Dockerfile

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "main.py"]
```

### Production Dockerfile

```dockerfile
FROM python:3.11-slim AS base

# Security: non-root user
RUN useradd --create-home appuser

FROM base AS deps
WORKDIR /home/appuser/app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM base
USER appuser
WORKDIR /home/appuser/app
COPY --from=deps /usr/local/lib/python3.11 /usr/local/lib/python3.11
COPY --chown=appuser . .

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD python -c "import polyai; print('ok')"

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
docker build -t myapp:latest .
docker run -p 8000:8000 \
  -e OVHCLOUD_API_KEY="your-key" \
  myapp:latest
```

---

## AWS Lambda

```python
# handler.py
import json
from polyai import Client

# Create client outside the handler — reused across warm invocations
client = Client()

def lambda_handler(event, context):
    body = json.loads(event.get("body", "{}"))
    message = body.get("message", "")

    if not message:
        return {"statusCode": 400, "body": json.dumps({"error": "No message"})}

    try:
        response = client.chat(
            provider="ovhcloud",
            model="llama-3.1-8b-instruct",
            messages=[{"role": "user", "content": message}],
            max_tokens=200,
            timeout=30.0,  # Lambda has max 15 min; set conservative timeout
        )
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"text": response.text}),
        }
    except Exception as e:
        return {"statusCode": 502, "body": json.dumps({"error": str(e)})}
```

`requirements.txt` for Lambda:
```
polyai==1.0.0
```

Deploy with SAM, Serverless Framework, or CDK.

---

## Google Cloud Run

```yaml
# cloudbuild.yaml
steps:
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/polyai-app', '.']
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/polyai-app']
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    args:
      - gcloud
      - run
      - deploy
      - polyai-app
      - --image=gcr.io/$PROJECT_ID/polyai-app
      - --region=europe-west1
      - --platform=managed
      - --set-secrets=OVHCLOUD_API_KEY=ovhcloud-key:latest
```

---

## Heroku

```bash
heroku create my-polyai-app
heroku config:set OVHCLOUD_API_KEY="your-key"
heroku config:set UNIVERSAL_AI_TIMEOUT=45
git push heroku main
```

`Procfile`:
```
web: uvicorn main:app --host 0.0.0.0 --port $PORT
```

---

## Kubernetes

See the complete example in [Production Guide](production-guide.md#kubernetes-deployment).

---

## Platform-Specific Notes

### Vercel / Edge Functions

PolyAI is not designed for edge runtimes (no Python support). Use a Node.js HTTP client to call your Python backend instead.

### Render

```yaml
# render.yaml
services:
  - type: web
    name: polyai-app
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: OVHCLOUD_API_KEY
        sync: false  # set manually in dashboard
```

---

## Monitoring After Deployment

After deploying, verify:

```bash
# Health check
curl https://your-app.example.com/healthz

# Test endpoint
curl -X POST https://your-app.example.com/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "ping"}'
```

Set up alerts for:
- Error rate > 5% → page on-call
- p95 latency > 10s → investigate provider
- Memory usage > 80% → scale up
