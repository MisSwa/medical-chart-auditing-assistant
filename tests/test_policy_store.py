import os
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from policy_store import build_faiss_index, chunk_text, retrieve_policy_chunks


def test_chunk_text_produces_correct_sizes():
    text = "A" * 100 + "B" * 100  # 200 chars
    chunk_size = 100
    overlap = 20
    chunks = chunk_text(text, chunk_size=chunk_size, overlap=overlap)

    for chunk in chunks:
        assert len(chunk) <= chunk_size

    # Verify overlap: end of chunk[i] equals start of chunk[i+1]
    for i in range(len(chunks) - 1):
        assert chunks[i][-overlap:] == chunks[i + 1][:overlap], (
            f"Overlap mismatch between chunks {i} and {i + 1}"
        )


def test_chunk_text_covers_full_document():
    text = "abcde" * 500  # 2500 chars
    chunk_size = 1000
    overlap = 100
    chunks = chunk_text(text, chunk_size=chunk_size, overlap=overlap)

    step = chunk_size - overlap  # 900
    for i, chunk in enumerate(chunks):
        start = i * step
        expected = text[start : start + chunk_size]
        assert chunk == expected, f"Chunk {i} does not match expected slice of source text"


def test_build_faiss_index_stores_all_chunks():
    import faiss

    chunks = ["chunk one", "chunk two", "chunk three"]
    dim = 8
    embeddings = [np.random.rand(dim).tolist() for _ in chunks]
    index, returned_chunks = build_faiss_index(chunks, embeddings)

    assert index.ntotal == len(chunks)
    assert returned_chunks == chunks


def test_retrieve_returns_k_results():
    dim = 8
    chunks = [f"policy chunk {i}" for i in range(10)]
    embeddings = [np.random.rand(dim).tolist() for _ in chunks]
    index, indexed_chunks = build_faiss_index(chunks, embeddings)

    fake_embedding = np.random.rand(dim).tolist()

    with patch("policy_store._get_openai_client") as mock_get_client:
        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=fake_embedding)]
        mock_get_client.return_value.embeddings.create.return_value = mock_response

        results = retrieve_policy_chunks("test query", index, indexed_chunks, k=5)

    assert len(results) == 5
    for r in results:
        assert r in chunks


@pytest.mark.integration
def test_retrieve_integration():
    if not os.environ.get("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set — skipping integration test")

    from policy_store import embed_chunks

    policy_text = (
        "Coverage for Type 2 Diabetes management requires a confirmed diagnosis "
        "with ICD-10 code E11.x. Patients must have a documented HbA1c greater "
        "than 7.5 percent. Prior authorization is required for all GLP-1 receptor agonists."
    )
    chunks = [policy_text]
    embeddings = embed_chunks(chunks)
    index, indexed_chunks = build_faiss_index(chunks, embeddings)

    results = retrieve_policy_chunks(
        "Type 2 Diabetes ICD-10 coverage requirements", index, indexed_chunks, k=1
    )
    assert len(results) >= 1
    assert "E11" in results[0] or "Diabetes" in results[0]
