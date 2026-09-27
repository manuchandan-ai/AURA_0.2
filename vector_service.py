import math
import requests
from typing import List, Dict, Any

OLLAMA_EMBED_URL = "http://localhost:11434/api/embeddings"
EMBED_MODEL = "nomic-embed-text"

def get_embedding(text: str) -> List[float]:
    """Generates a dense vector embedding using local Ollama nomic-embed-text."""
    try:
        res = requests.post(OLLAMA_EMBED_URL, json={"model": EMBED_MODEL, "prompt": text}, timeout=15)
        if res.status_code == 200:
            return res.json().get("embedding", [])
    except Exception:
        pass
    return []

def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """Computes cosine similarity between two float vectors."""
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)

def chunk_text(text: str, chunk_size: int = 600, overlap: int = 100) -> List[str]:
    """Splits a document into overlapping semantic chunks."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += (chunk_size - overlap)
    return chunks

class LocalRAGService:
    @staticmethod
    def rank_relevant_chunks(query: str, doc_text: str, top_k: int = 3) -> List[str]:
        chunks = chunk_text(doc_text)
        if not chunks:
            return []
        
        # If document is small enough to fit in a single chunk, return it directly
        if len(chunks) <= top_k:
            return chunks

        query_vec = get_embedding(query)
        if not query_vec:
            # Fallback if Ollama embeddings are temporarily unreachable
            return chunks[:top_k]

        scored_chunks = []
        for c in chunks:
            c_vec = get_embedding(c)
            sim = cosine_similarity(query_vec, c_vec)
            scored_chunks.append((sim, c))

        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        return [chunk for _, chunk in scored_chunks[:top_k]]