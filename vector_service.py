# vector_service.py
import math
import hashlib
import json
import logging
import requests
from typing import List, Tuple
from langchain_text_splitters import RecursiveCharacterTextSplitter
from database import SessionLocal, ArtifactChunk

logger = logging.getLogger("AURA-VectorService")

OLLAMA_EMBED_URL = "http://localhost:11434/api/embeddings"
EMBED_MODEL = "nomic-embed-text"

def get_embedding(text: str) -> List[float]:
    """Generates a dense vector embedding using local Ollama nomic-embed-text."""
    try:
        res = requests.post(
            OLLAMA_EMBED_URL,
            json={"model": EMBED_MODEL, "prompt": text},
            timeout=15
        )
        if res.status_code == 200:
            return res.json().get("embedding", [])
    except Exception as e:
        logger.warning(f"Ollama embedding failure: {e}")
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

def semantic_chunk_document(text: str, chunk_size: int = 800, chunk_overlap: int = 120) -> List[str]:
    """
    Context-aware semantic splitting using boundary heuristics
    (Markdown headers, code blocks, paragraphs, and sentences).
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n## ", "\n### ", "\n```", "\n\n", "\n", ". ", " ", ""]
    )
    return [c.strip() for c in splitter.split_text(text) if c.strip()]

class LocalRAGService:
    @staticmethod
    def index_artifact_chunks(artifact_id: int, doc_text: str):
        """Indexes and precomputes embeddings once at upload time."""
        chunks = semantic_chunk_document(doc_text)
        if not chunks:
            return

        db = SessionLocal()
        try:
            # Delete stale chunks for this artifact if re-indexing
            db.query(ArtifactChunk).filter(ArtifactChunk.artifact_id == artifact_id).delete()

            for idx, chunk_content in enumerate(chunks):
                ch_hash = hashlib.sha256(chunk_content.encode("utf-8")).hexdigest()
                vector = get_embedding(chunk_content)
                chunk_record = ArtifactChunk(
                    artifact_id=artifact_id,
                    chunk_index=idx,
                    content=chunk_content,
                    content_hash=ch_hash,
                    embedding_json=json.dumps(vector) if vector else None
                )
                db.add(chunk_record)
            db.commit()
            logger.info(f"Indexed {len(chunks)} precomputed chunks for artifact {artifact_id}.")
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to index chunks for artifact {artifact_id}: {e}")
        finally:
            db.close()

    @staticmethod
    def rank_relevant_chunks(query: str, artifact_id: int, top_k: int = 3) -> List[str]:
        """Queries precomputed SQLite vectors instead of re-embedding the whole document."""
        db = SessionLocal()
        try:
            stored_chunks = db.query(ArtifactChunk).filter(ArtifactChunk.artifact_id == artifact_id).all()
            if not stored_chunks:
                return []

            query_vec = get_embedding(query)
            if not query_vec:
                return [c.content for c in stored_chunks[:top_k]]

            scored: List[Tuple[float, str]] = []
            for sc in stored_chunks:
                if sc.embedding_json:
                    c_vec = json.loads(sc.embedding_json)
                    sim = cosine_similarity(query_vec, c_vec)
                    scored.append((sim, sc.content))
                else:
                    scored.append((0.0, sc.content))

            scored.sort(key=lambda x: x[0], reverse=True)
            return [chunk_text for _, chunk_text in scored[:top_k]]
        finally:
            db.close()