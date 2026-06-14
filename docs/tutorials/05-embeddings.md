# Tutorial 5: Embeddings & Semantic Search

> **Level:** Intermediate | **Time:** 20 minutes
> **Repository:** https://github.com/Alqudimi/PolyAI

---

## Goals

- Generate text embeddings
- Compute cosine similarity
- Build a semantic search system
- Understand when to use embeddings

---

## What are Embeddings?

Embeddings convert text into high-dimensional vectors (lists of numbers). Texts with similar meaning produce similar vectors. This enables:

- **Semantic search** — find documents by meaning, not keywords
- **Clustering** — group similar texts automatically
- **Classification** — categorise text by similarity to examples
- **Anomaly detection** — find texts that don't fit a category

```
"Hello world"     → [0.12, -0.34, 0.78, ...]  (1024 numbers)
"Hi there"        → [0.13, -0.35, 0.77, ...]  (very similar → similar meaning)
"Quantum physics" → [-0.92, 0.41, -0.23, ...] (very different → different meaning)
```

---

## Step 1: Generate Embeddings

```python
from polyai import Client

client = Client()

result = client.embed(
    provider="ovhcloud",
    input="Python is a popular programming language.",
    model="bge-m3",
)

embedding = result.embeddings[0]
print(f"Dimensions: {embedding.dimensions}")         # e.g., 1024
print(f"First 5 values: {embedding.vector[:5]}")     # [-0.02, 0.01, ...]
```

---

## Step 2: Similarity Between Two Texts

```python
from polyai import Client

client = Client()

result = client.embed(
    provider="ovhcloud",
    input=[
        "Python is a programming language",
        "Python is a type of snake",
        "JavaScript runs in the browser",
    ],
    model="bge-m3",
)

e1, e2, e3 = result.embeddings

print(f"Python prog vs Python snake: {e1.cosine_similarity(e2):.4f}")
print(f"Python prog vs JavaScript:   {e1.cosine_similarity(e3):.4f}")
print(f"Python snake vs JavaScript:  {e2.cosine_similarity(e3):.4f}")
```

Typical output:
```
Python prog vs Python snake: 0.7234   (similar word, different meaning)
Python prog vs JavaScript:   0.8912   (both programming languages)
Python snake vs JavaScript:  0.4231   (least related)
```

---

## Step 3: Similarity Matrix

For multiple texts, get all pairwise similarities at once:

```python
result = client.embed(
    provider="ovhcloud",
    input=["cat", "dog", "python", "javascript", "biology"],
    model="bge-m3",
)

matrix = result.similarity_matrix()

labels = ["cat", "dog", "python", "javascript", "biology"]
print("     ", "  ".join(f"{l:10}" for l in labels))
for i, row in enumerate(matrix):
    print(f"{labels[i]:5}", "  ".join(f"{v:10.4f}" for v in row))
```

---

## Step 4: Semantic Search

Build a simple search engine that finds the most relevant document:

```python
from polyai import Client

client = Client()

# Your knowledge base
documents = [
    "Python is a high-level programming language known for its readability.",
    "JavaScript is the primary language for web browser scripting.",
    "Docker is a containerisation platform for packaging applications.",
    "Machine learning is a subset of AI that learns from data.",
    "PostgreSQL is an open-source relational database system.",
    "Kubernetes orchestrates containerised applications at scale.",
    "NumPy provides numerical computing capabilities for Python.",
    "FastAPI is a modern Python framework for building APIs.",
]

# Embed all documents (do this once, cache the results)
doc_result = client.embed(
    provider="ovhcloud",
    input=documents,
    model="bge-m3",
)
doc_embeddings = doc_result.embeddings

def search(query: str, top_k: int = 3) -> list[tuple[str, float]]:
    """Find the top_k most relevant documents."""
    query_result = client.embed(
        provider="ovhcloud",
        input=query,
        model="bge-m3",
    )
    query_embedding = query_result.embeddings[0]

    # Score each document
    scores = [
        (doc, query_embedding.cosine_similarity(doc_emb))
        for doc, doc_emb in zip(documents, doc_embeddings)
    ]

    # Sort by score (highest first)
    scores.sort(key=lambda x: x[1], reverse=True)
    return scores[:top_k]


# Test it
results = search("How do I run containers?", top_k=3)
print("Query: 'How do I run containers?'\n")
for doc, score in results:
    print(f"  [{score:.4f}] {doc}")
```

Output:
```
Query: 'How do I run containers?'

  [0.7823] Docker is a containerisation platform for packaging applications.
  [0.7412] Kubernetes orchestrates containerised applications at scale.
  [0.5234] PostgreSQL is an open-source relational database system.
```

---

## Step 5: Efficient Batch Embedding

For large document sets, send texts in batches:

```python
from polyai import Client

client = Client()

def batch_embed(texts: list[str], batch_size: int = 100) -> list[list[float]]:
    """Embed a large list of texts in batches."""
    all_vectors = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        result = client.embed(
            provider="ovhcloud",
            input=batch,
            model="bge-m3",
        )
        all_vectors.extend(emb.vector for emb in result.embeddings)
        print(f"Embedded {min(i + batch_size, len(texts))}/{len(texts)}")

    return all_vectors


# Embed 1000 documents
import random, string

texts = ["".join(random.choices(string.ascii_lowercase + " ", k=50)) for _ in range(1000)]
vectors = batch_embed(texts, batch_size=100)
print(f"Embedded {len(vectors)} texts, each {len(vectors[0])} dimensions")
```

---

## Step 6: Async Embedding

For high-throughput applications:

```python
import asyncio
from polyai import AsyncClient

async def embed_many(texts: list[str]) -> list[list[float]]:
    async with AsyncClient() as client:
        # Send all in one call
        result = await client.embed(
            provider="ovhcloud",
            input=texts,
            model="bge-m3",
        )
        return [emb.vector for emb in result.embeddings]

texts = ["text one", "text two", "text three"]
vectors = asyncio.run(embed_many(texts))
```

---

## Embedding Models

| Provider | Model | Dimensions | Languages | Notes |
|---|---|---|---|---|
| OVHcloud | `bge-m3` | 1024 | 100+ | Best quality, multilingual |
| OVHcloud | `bge-large-en-v1.5` | 1024 | English | Fast, English-only |
| OVHcloud | `nomic-embed-text-v1.5` | 768 | English | Compact |
| Pollinations | (varies) | varies | varies | |

---

## Storing Embeddings

For production, store embeddings in a vector database:

```python
# Example with numpy (simple, in-memory)
import numpy as np
import pickle

# Save
vectors_array = np.array([emb.vector for emb in result.embeddings])
with open("embeddings.pkl", "wb") as f:
    pickle.dump({"vectors": vectors_array, "texts": documents}, f)

# Load
with open("embeddings.pkl", "rb") as f:
    data = pickle.load(f)

# Search
def cosine_similarity_batch(query_vec, doc_vecs):
    """Fast batch cosine similarity using numpy."""
    query_norm = query_vec / np.linalg.norm(query_vec)
    doc_norms = doc_vecs / np.linalg.norm(doc_vecs, axis=1, keepdims=True)
    return (doc_norms @ query_norm).tolist()
```

For large-scale production, consider:
- **pgvector** — PostgreSQL extension
- **Pinecone** — managed vector database
- **Qdrant** — open-source vector database
- **Chroma** — simple local vector store

---

## Next Steps

- [Tutorial 6: Production](06-production.md) — deploy your app
- [Tutorial 7: Custom Provider](07-custom-provider.md) — add a new provider
