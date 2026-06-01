"""
Policy document ingestion, embedding, FAISS indexing, and RAG retrieval.
"""
import os

import faiss
import numpy as np
from langsmith import traceable
from openai import OpenAI

from extractor import extract_text

CHUNK_SIZE = 1000
OVERLAP = 100
EMBEDDING_MODEL = "text-embedding-3-small"
TOP_K = 5


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = OVERLAP) -> list[str]:
    """Fixed-size character chunking with overlap. Returns list of chunk strings."""
    chunks = []
    start = 0
    while start < len(text):
        chunks.append(text[start : start + chunk_size])
        end = start + chunk_size
        if end >= len(text):
            break
        start += chunk_size - overlap
    return chunks


@traceable(name="embed_chunks", run_type="embedding")
def embed_chunks(chunks: list[str]) -> list[list[float]]:
    """Embed a list of text chunks using text-embedding-3-small. Returns list of float vectors."""
    client = _get_openai_client()
    response = client.embeddings.create(model=EMBEDDING_MODEL, input=chunks)
    return [item.embedding for item in response.data]


def build_faiss_index(chunks: list[str], embeddings: list[list[float]]):
    """
    Build an in-memory FAISS IndexFlatL2 from chunk embeddings.
    Returns (index, chunks) tuple.
    """
    vectors = np.array(embeddings, dtype="float32")
    dim = vectors.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(vectors)
    return index, chunks


@traceable(name="retrieve_policy_chunks", run_type="retriever")
def retrieve_policy_chunks(query: str, index, chunks: list[str], k: int = TOP_K) -> list[str]:
    """
    Embed query and return the top-k most relevant policy chunks from the FAISS index.
    Returns list of chunk strings ordered by relevance.
    """
    client = _get_openai_client()
    response = client.embeddings.create(model=EMBEDDING_MODEL, input=[query])
    query_vector = np.array([response.data[0].embedding], dtype="float32")
    _, indices = index.search(query_vector, k)
    return [chunks[i] for i in indices[0] if i < len(chunks)]


@traceable(name="ingest_policy_document")
def ingest_policy_document(filepath: str):
    """
    Orchestrate full policy ingestion: extract text → chunk → embed → build index.
    Returns (index, chunks) tuple stored in session state.
    """
    text = extract_text(filepath)
    chunks = chunk_text(text)
    embeddings = embed_chunks(chunks)
    return build_faiss_index(chunks, embeddings)


def _get_openai_client() -> OpenAI:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "OPENAI_API_KEY is not set. "
            "Add it to your .env file or set it as an environment variable."
        )
    return OpenAI(api_key=api_key)
