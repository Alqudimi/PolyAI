"""
Production Example: FastAPI AI Service

A complete FastAPI application using PolyAI with:
- Proper async client lifecycle (startup/shutdown)
- Provider failover
- Structured error responses
- Request IDs for tracing
- Health check endpoint
- Streaming endpoint (SSE)
- Pydantic request validation

Usage:
    pip install fastapi uvicorn
    uvicorn examples.production.with_fastapi:app --reload

Test with:
    curl -X POST http://localhost:8000/api/v1/chat \\
      -H "Content-Type: application/json" \\
      -d '{"message": "What is Python?"}'

    curl "http://localhost:8000/api/v1/stream?message=Count+from+1+to+5"
"""

from __future__ import annotations

import logging
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from polyai import AsyncClient, ClientConfig
from polyai.config import ProviderConfig
from polyai.exceptions import (
    AuthenticationError,
    RateLimitError,
    ProviderUnavailableError,
    UniversalAIError,
)

# ──────────────────────────────────────────────────────────────────────────────
# Logging
# ──────────────────────────────────────────────────────────────────────────────

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Global client (one per application lifetime)
# ──────────────────────────────────────────────────────────────────────────────

_client: AsyncClient | None = None


def get_client() -> AsyncClient:
    assert _client is not None, "Client not initialised"
    return _client


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create client at startup, close at shutdown."""
    global _client
    logger.info("Starting PolyAI client...")
    config = ClientConfig(
        timeout=45.0,
        max_retries=3,
        providers={
            "mlvoca": ProviderConfig(timeout=120.0, max_retries=1),
        },
    )
    _client = AsyncClient(config=config)
    logger.info("PolyAI client ready.")
    yield
    logger.info("Shutting down PolyAI client...")
    await _client.aclose()
    logger.info("PolyAI client closed.")


# ──────────────────────────────────────────────────────────────────────────────
# FastAPI app
# ──────────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="PolyAI Demo API",
    description="A production-grade AI API powered by PolyAI",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# ──────────────────────────────────────────────────────────────────────────────
# Request / Response models
# ──────────────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10_000, description="User message")
    provider: str = Field("ovhcloud", description="AI provider")
    model: str = Field("llama-3.1-8b-instruct", description="Model ID")
    max_tokens: int = Field(500, ge=1, le=4_000)
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    system: str | None = Field(None, description="Optional system prompt")


class ChatResponse(BaseModel):
    text: str
    request_id: str
    provider: str
    model: str
    tokens_used: int


class ErrorResponse(BaseModel):
    error: str
    request_id: str
    code: str


# ──────────────────────────────────────────────────────────────────────────────
# Failover helper
# ──────────────────────────────────────────────────────────────────────────────

FALLBACK_PROVIDERS = [
    ("ovhcloud",     "llama-3.1-8b-instruct"),
    ("pollinations", "openai"),
]


async def chat_with_failover(
    messages: list[dict],
    max_tokens: int,
    temperature: float,
    request_id: str,
    preferred_provider: str | None = None,
    preferred_model: str | None = None,
):
    """Chat with automatic failover to backup providers."""
    chain = list(FALLBACK_PROVIDERS)
    if preferred_provider and preferred_model:
        chain.insert(0, (preferred_provider, preferred_model))

    last_error: Exception | None = None
    for provider, model in chain:
        try:
            response = await get_client().chat(
                provider=provider,
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            logger.info(
                "chat_ok request_id=%s provider=%s model=%s tokens=%d",
                request_id, provider, model, response.usage.total_tokens,
            )
            return response, provider, model
        except AuthenticationError:
            raise  # don't failover for auth errors
        except (RateLimitError, ProviderUnavailableError, UniversalAIError) as e:
            logger.warning("chat_fail provider=%s error=%s", provider, e)
            last_error = e
            continue

    raise last_error or RuntimeError("All providers failed")


# ──────────────────────────────────────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────────────────────────────────────

@app.get("/healthz", tags=["infra"])
async def health():
    """Health check endpoint."""
    return {"status": "ok", "service": "polyai-demo"}


@app.post(
    "/api/v1/chat",
    response_model=ChatResponse,
    tags=["AI"],
    summary="Send a chat message",
)
async def chat(req: ChatRequest):
    """Send a message and receive a complete response."""
    request_id = str(uuid.uuid4())
    messages = [{"role": "user", "content": req.message}]
    if req.system:
        messages.insert(0, {"role": "system", "content": req.system})

    try:
        response, used_provider, used_model = await chat_with_failover(
            messages=messages,
            max_tokens=req.max_tokens,
            temperature=req.temperature,
            request_id=request_id,
            preferred_provider=req.provider,
            preferred_model=req.model,
        )
        return ChatResponse(
            text=response.text,
            request_id=request_id,
            provider=used_provider,
            model=used_model,
            tokens_used=response.usage.total_tokens,
        )

    except AuthenticationError:
        raise HTTPException(status_code=500, detail="AI service configuration error")
    except UniversalAIError as e:
        raise HTTPException(status_code=502, detail=f"AI service error: {e}")
    except Exception:
        logger.exception("Unexpected error request_id=%s", request_id)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get(
    "/api/v1/stream",
    tags=["AI"],
    summary="Stream a chat response (SSE)",
    response_class=StreamingResponse,
)
async def stream_chat(
    message: str = Query(..., min_length=1, description="User message"),
    max_tokens: int = Query(300, ge=1, le=4000),
):
    """Stream a chat response as Server-Sent Events."""
    request_id = str(uuid.uuid4())
    messages = [{"role": "user", "content": message}]

    async def generate():
        try:
            async for chunk in await get_client().chat_stream(
                provider="ovhcloud",
                model="llama-3.1-8b-instruct",
                messages=messages,
                max_tokens=max_tokens,
            ):
                if chunk.delta:
                    yield f"data: {chunk.delta}\n\n"
            yield "data: [DONE]\n\n"
        except UniversalAIError as e:
            yield f"data: ERROR: {e}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "X-Request-ID": request_id,
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
