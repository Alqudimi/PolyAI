"""
embeddings_similarity.py — Semantic similarity with OVHcloud BGE embeddings.

Demonstrates embedding generation, cosine similarity, and similarity matrices.
Requires an OVHcloud API key (or uses anonymous free tier with rate limits).
"""

from polyai import Client

client = Client()

# ── Single embedding ──────────────────────────────────────────────────────

result = client.embed(
    provider="ovhcloud",
    input="The quick brown fox jumps over the lazy dog.",
    model="bge-m3",
)
embedding = result.first
print(f"Embedding dimensions: {embedding.dimensions}")
print(f"First 5 values: {embedding.vector[:5]}")


# ── Semantic similarity comparison ───────────────────────────────────────

sentences = [
    "I love programming in Python.",
    "Python is my favourite coding language.",
    "The sky is blue today.",
    "I enjoy writing software.",
]

result = client.embed(provider="ovhcloud", input=sentences, model="bge-m3")

print("\n=== Pairwise Cosine Similarities ===")
for i in range(len(sentences)):
    for j in range(i + 1, len(sentences)):
        sim = result.embeddings[i].cosine_similarity(result.embeddings[j])
        print(f"[{i}]↔[{j}]: {sim:.4f}  | \"{sentences[i][:40]}...\" vs \"{sentences[j][:40]}...\"")


# ── Similarity matrix ─────────────────────────────────────────────────────

print("\n=== Similarity Matrix ===")
matrix = result.similarity_matrix()
print(f"{'':>5}", end="")
for i in range(len(sentences)):
    print(f"  [{i}]  ", end="")
print()
for i, row in enumerate(matrix):
    print(f"[{i}]  ", end="")
    for val in row:
        print(f" {val:.3f}", end="")
    print()


# ── Nearest neighbour search ─────────────────────────────────────────────

query = "I write code every day."
all_texts = sentences + [query]
all_result = client.embed(provider="ovhcloud", input=all_texts, model="bge-m3")

query_emb = all_result.embeddings[-1]
print(f"\n=== Nearest neighbours for: '{query}' ===")
similarities = [
    (sentences[i], query_emb.cosine_similarity(all_result.embeddings[i]))
    for i in range(len(sentences))
]
for text, score in sorted(similarities, key=lambda x: x[1], reverse=True):
    print(f"  {score:.4f} — {text}")

client.close()
