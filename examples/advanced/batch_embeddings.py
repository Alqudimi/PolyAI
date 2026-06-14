"""
Advanced Example: Batch Embedding + Semantic Search

This example demonstrates:
- Embedding large sets of texts in batches
- Building a simple semantic search index
- Finding top-k similar texts
- Similarity matrix visualisation

Usage:
    python examples/advanced/batch_embeddings.py

Requires OVHCLOUD_API_KEY for higher rate limits (anonymous works but is slow).
"""

from __future__ import annotations

import time
from polyai import Client, ClientConfig
from polyai.exceptions import UniversalAIError


# ──────────────────────────────────────────────────────────────────────────────
# Sample document corpus
# ──────────────────────────────────────────────────────────────────────────────

DOCUMENTS = [
    # Programming languages
    "Python is a high-level, interpreted programming language known for readability.",
    "JavaScript runs natively in web browsers and is used for frontend development.",
    "Rust is a systems programming language focused on safety and performance.",
    "Go is a statically typed, compiled language designed for simplicity.",
    "TypeScript adds static types to JavaScript for better tooling.",

    # Frameworks
    "FastAPI is a modern Python framework for building REST APIs quickly.",
    "Django is a Python web framework that follows the MVC pattern.",
    "React is a JavaScript library for building user interfaces.",
    "Next.js is a React framework for server-side rendering and static sites.",
    "Express.js is a minimal Node.js framework for web applications.",

    # Databases
    "PostgreSQL is an open-source object-relational database system.",
    "MongoDB is a document-oriented NoSQL database.",
    "Redis is an in-memory data store used as cache and message broker.",
    "SQLite is a lightweight, serverless embedded database engine.",
    "Elasticsearch is a distributed search and analytics engine.",

    # AI/ML
    "TensorFlow is an open-source machine learning framework by Google.",
    "PyTorch is a deep learning framework popular in research.",
    "Scikit-learn provides simple tools for machine learning in Python.",
    "Hugging Face is a platform for sharing pre-trained NLP models.",
    "LangChain is a framework for building applications with LLMs.",

    # DevOps
    "Docker is a containerisation platform for packaging applications.",
    "Kubernetes orchestrates containerised workloads at scale.",
    "GitHub Actions automates CI/CD workflows directly in GitHub.",
    "Terraform enables infrastructure-as-code for cloud providers.",
    "Ansible automates server configuration and deployment.",
]


# ──────────────────────────────────────────────────────────────────────────────
# Embedding utilities
# ──────────────────────────────────────────────────────────────────────────────

def embed_batch(
    texts: list[str],
    client: Client,
    batch_size: int = 25,
    delay_between_batches: float = 1.0,
) -> list[list[float]]:
    """Embed a list of texts in batches. Returns list of vectors."""
    all_vectors: list[list[float]] = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        print(f"Embedding batch {i // batch_size + 1}/{(len(texts) - 1) // batch_size + 1} "
              f"({len(batch)} texts)...")

        try:
            result = client.embed(
                provider="ovhcloud",
                input=batch,
                model="bge-m3",
            )
            all_vectors.extend(emb.vector for emb in result.embeddings)

            if i + batch_size < len(texts):
                time.sleep(delay_between_batches)

        except UniversalAIError as e:
            print(f"  Error: {e}")
            # Fill with zero vectors on error
            all_vectors.extend([[0.0] * 1024 for _ in batch])

    return all_vectors


def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = sum(a * a for a in v1) ** 0.5
    norm2 = sum(b * b for b in v2) ** 0.5
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)


def search(
    query_vector: list[float],
    doc_vectors: list[list[float]],
    documents: list[str],
    top_k: int = 5,
) -> list[tuple[str, float]]:
    """Return top_k most similar documents."""
    scores = [
        (doc, cosine_similarity(query_vector, doc_vec))
        for doc, doc_vec in zip(documents, doc_vectors)
    ]
    scores.sort(key=lambda x: x[1], reverse=True)
    return scores[:top_k]


# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────

def main() -> None:
    config = ClientConfig(max_retries=2, timeout=60.0)
    client = Client(config=config)

    print(f"Embedding {len(DOCUMENTS)} documents...")
    print("-" * 50)
    start = time.perf_counter()

    doc_vectors = embed_batch(DOCUMENTS, client)

    elapsed = time.perf_counter() - start
    print(f"\nEmbedded {len(doc_vectors)} documents in {elapsed:.1f}s")
    print(f"Vector dimensions: {len(doc_vectors[0])}")

    # ── Search demo ────────────────────────────────────────────────
    queries = [
        "How do I build a REST API?",
        "What database should I use for caching?",
        "How do I deploy containers at scale?",
        "Which tools help with machine learning?",
    ]

    print("\n" + "=" * 60)
    print("SEMANTIC SEARCH DEMO")
    print("=" * 60)

    for query in queries:
        print(f"\nQuery: {query!r}")
        print("-" * 40)

        # Embed the query
        q_result = client.embed(provider="ovhcloud", input=query, model="bge-m3")
        q_vector = q_result.embeddings[0].vector

        # Search
        results = search(q_vector, doc_vectors, DOCUMENTS, top_k=3)

        for rank, (doc, score) in enumerate(results, 1):
            print(f"  {rank}. [{score:.4f}] {doc}")

    # ── Similarity matrix (subset) ─────────────────────────────────
    print("\n" + "=" * 60)
    print("SIMILARITY MATRIX (first 5 documents)")
    print("=" * 60)

    labels = [doc.split()[0] for doc in DOCUMENTS[:5]]
    subset = doc_vectors[:5]

    print(f"{'':12}", end="")
    for label in labels:
        print(f"{label:12}", end="")
    print()

    for i, (label_i, vec_i) in enumerate(zip(labels, subset)):
        print(f"{label_i:12}", end="")
        for vec_j in subset:
            sim = cosine_similarity(vec_i, vec_j)
            print(f"{sim:12.4f}", end="")
        print()


if __name__ == "__main__":
    main()
