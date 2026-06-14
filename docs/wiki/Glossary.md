# Glossary

> **Repository:** https://github.com/Alqudimi/PolyAI

Definitions of terms used in PolyAI documentation.

---

## A

### API (Application Programming Interface)
A set of rules and protocols that allow software to communicate with other software. PolyAI provides a Python API for communicating with AI providers.

### API Key
A secret string used to authenticate your requests to an AI provider. Some providers (OVHcloud, Pollinations) allow limited anonymous access without a key.

### Async / Asynchronous
A programming model where operations don't block the program while waiting for a response. PolyAI's `AsyncClient` enables async usage. See [AsyncClient](../api/client.md).

### Accumulator
A component that collects streaming chunks into a complete response. PolyAI provides `StreamAccumulator` and `AsyncStreamAccumulator`.

---

## B

### Backoff
A delay between retry attempts. PolyAI uses exponential backoff with full jitter. See [Retry Policy](../dev/architecture.md#layer-5-retry-policy).

### Base URL
The root URL of a provider's API. For OVHcloud: `https://oai.endpoints.kepler.ai.cloud.ovh.net/v1`.

### BGE-M3
A multilingual embedding model from BAAI (Beijing Academy of AI), available via OVHcloud. Supports 100+ languages.

---

## C

### Chat Completion
The process of sending a conversation history (messages) to an AI model and receiving a response. Core feature of all four PolyAI providers.

### ChatResponse
The object returned by `client.chat()`. Contains `.text`, `.usage`, `.finish_reason`, `.tool_calls`, and `.raw`. See [Types Reference](../api/types.md).

### ChatChunk
One token-group yielded by `client.chat_stream()`. Contains `.delta` (new text) and `.finish_reason`.

### CODEOWNERS
A GitHub file that specifies who must review changes to specific files. PolyAI uses CODEOWNERS to protect auth and CI/CD files.

### Connection Pool
A cache of open HTTP connections reused across requests. PolyAI's client maintains a connection pool, which is why reusing the `Client` object is important for performance.

### Content Filter
A safety system that blocks or modifies requests/responses that violate the provider's content policy. PolyAI raises `ContentFilterError` when triggered.

### Context Length
The maximum number of tokens a model can process in one request (input + output combined). Exceeding this raises `ContextLengthExceededError`.

### Conventional Commits
A commit message format like `feat(scope): description`. PolyAI enforces this format for all commits.

### Cosine Similarity
A mathematical measure of similarity between two vectors, ranging from -1 (opposite) to 1 (identical). Used to compare embeddings. Values above 0.8 typically indicate semantically similar texts.

---

## D

### Delta
The incremental text in a streaming chunk. `chunk.delta` is the new text generated since the last chunk.

### DevToolbox API
One of PolyAI's four supported providers. Offers AI utilities (summarise, translate, explain code) plus developer tools (UUID, password, QR code). Hosted on Cloudflare Workers.

---

## E

### Embedding
A numerical representation of text as a high-dimensional vector. Similar texts produce similar embeddings. Used for semantic search, clustering, and classification.

### EmbeddingResponse
The object returned by `client.embed()`. Contains `embeddings` (list of `Embedding`), `model`, `provider`, `usage`. See [Types Reference](../api/types.md).

### Exponential Backoff
A retry strategy where the wait time doubles after each failed attempt. PolyAI adds full jitter to prevent thundering herd issues.

---

## F

### Failover
Automatically switching to a different provider when one fails or is unavailable. PolyAI doesn't implement automatic failover — you implement it by catching exceptions.

### Finish Reason
Why the model stopped generating. Common values: `"stop"` (natural end), `"length"` (hit max_tokens), `"tool_calls"` (model wants to call a function).

### Function Calling
See **Tool Use**.

### Full Jitter
A retry backoff strategy where the actual wait time is chosen randomly from `[0, exponential_cap]`. Prevents multiple clients from retrying simultaneously.

---

## G

### GDPR
General Data Protection Regulation — EU data privacy law. OVHcloud AI Endpoints is EU-hosted and supports GDPR compliance.

---

## H

### httpx
The HTTP client library used internally by PolyAI. Provides both sync and async support, HTTP/2, streaming, and connection pooling.

---

## J

### JSON Mode
A request setting that forces the model to return valid JSON. Set via `json_mode=True` in PolyAI. Supported by OVHcloud and Pollinations.

### Jitter
Random variation added to retry delays to prevent multiple clients from retrying simultaneously (thundering herd problem).

---

## L

### LLaMA
Large Language Model by Meta. Several variants are available on OVHcloud and mlvoca.

### LLM (Large Language Model)
A machine learning model trained on large amounts of text, capable of generating human-like text. Examples: LLaMA, GPT-4, Claude, Mistral.

---

## M

### Message
A dict with `"role"` and `"content"` keys representing one turn in a conversation. Roles: `"system"`, `"user"`, `"assistant"`, `"tool"`.

### mlvoca
One of PolyAI's four supported providers. Offers free, non-commercial LLM access via an Ollama-compatible API.

### Model
A specific AI neural network. Each provider offers multiple models with different capabilities, speeds, and costs. Example: `"llama-3.1-8b-instruct"`.

### Multimodal
Able to process multiple types of input (e.g., text + images). Vision-capable models are multimodal.

---

## O

### OIDC (OpenID Connect)
An authentication protocol. PolyAI uses OIDC Trusted Publishing for PyPI releases (no PyPI token secret needed).

### Ollama
A local LLM runtime that provides an API for running models locally. mlvoca uses an Ollama-compatible API format.

### OVHcloud AI Endpoints
One of PolyAI's four supported providers. EU-hosted, OpenAI-compatible, with 40+ open-source models.

---

## P

### Provider
An AI service PolyAI integrates with. PolyAI supports: OVHcloud, Pollinations, mlvoca, DevToolbox.

### Provider Adapter
A class implementing `BaseProvider` that translates PolyAI's unified API to a specific provider's HTTP format.

### Pollinations.AI
One of PolyAI's four supported providers. Free, no-signup access to chat, image generation, and TTS.

---

## R

### Rate Limit
A maximum number of requests per time period enforced by a provider. PolyAI automatically retries on 429 Rate Limit errors.

### Reranking
Scoring a list of documents by their relevance to a query. OVHcloud provides reranking models (BGE-reranker).

### Retry
Automatically re-sending a failed request. PolyAI retries on HTTP 429, 500, 502, 503, 504, and network errors.

---

## S

### SDK (Software Development Kit)
A library that makes it easier to interact with a service. PolyAI is an SDK for AI providers.

### SSE (Server-Sent Events)
A protocol for streaming data from server to client over HTTP. PolyAI uses SSE to implement real-time streaming.

### Semantic Search
Finding documents by meaning rather than exact keyword matches. Implemented using embeddings and cosine similarity.

### Streaming
Receiving AI output incrementally as it's generated, rather than waiting for the complete response. Implemented via SSE.

### System Prompt
A special message with `"role": "system"` that instructs the AI model how to behave. PolyAI also supports a `system` parameter shorthand.

---

## T

### Temperature
A parameter controlling randomness in AI output. 0.0 = deterministic (always the same output). 2.0 = very random.

### Thundering Herd
When many clients retry simultaneously, overwhelming a server. PolyAI's full jitter backoff prevents this.

### Timeout
Maximum time to wait for a response before raising `TimeoutError`. Default: 60 seconds.

### TLS (Transport Layer Security)
Encryption protocol for HTTPS. PolyAI always validates TLS certificates and never disables verification.

### Token
The basic unit of text that AI models process. A token is roughly 4 characters or ¾ of a word in English.

### Tool Call
A model's request to execute a function. Part of the function calling / agentic workflow.

### Tool Use / Function Calling
Giving AI models the ability to request execution of predefined functions. Enables agentic AI applications.

### Top-P (Nucleus Sampling)
A parameter that limits the vocabulary pool to the top tokens whose cumulative probability exceeds `top_p`. Alternative to temperature.

### TTS (Text-to-Speech)
Converting text to spoken audio. Supported by Pollinations.AI via PolyAI.

---

## U

### UniversalAIError
The base exception class for all PolyAI errors. Catch this to handle any provider error.

### Usage
Token usage statistics: `prompt_tokens`, `completion_tokens`, `total_tokens`. Available in `response.usage`.

---

## V

### Vector
A list of numbers representing text as coordinates in high-dimensional space. Embeddings are vectors.

### Vision
The ability to process images alongside text. Vision-capable (multimodal) models.

---

## W

### Whisper
OpenAI's speech-to-text model. Available on OVHcloud AI Endpoints as `whisper-large-v3-turbo`.
