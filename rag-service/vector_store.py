import os
import json
import math
import re
from pathlib import Path
from threading import Lock
from dotenv import load_dotenv
from google import genai
from google.genai import types
load_dotenv(Path(__file__).with_name(".env"))

STORE_DIRECTORY = Path(__file__).with_name("vector_data")
STORE_DIRECTORY.mkdir(exist_ok=True)
STORE_LOCK = Lock()

_ai_client = None


def get_ai_client():
    global _ai_client
    if _ai_client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not set in environment or .env file.")
        _ai_client = genai.Client(api_key=api_key)
    return _ai_client


def _project_file(project_id: str) -> Path:
    safe_id = re.sub(r"[^a-zA-Z0-9_.-]", "_", project_id)
    if not safe_id:
        raise ValueError("project_id must contain at least one valid character")
    return STORE_DIRECTORY / f"{safe_id}.json"


def _embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []

    client_instance = get_ai_client()
    embeddings = []
    for start in range(0, len(texts), 8):
        text_batch = texts[start:start + 8]
        response = client_instance.models.embed_content(
            model="gemini-embedding-001",
            contents=text_batch,
            config=types.EmbedContentConfig(output_dimensionality=768),
        )
        batch_embeddings = response.embeddings or []
        if len(batch_embeddings) != len(text_batch):
            raise RuntimeError(
                "Gemini returned an unexpected number of embeddings "
                f"({len(batch_embeddings)} for {len(text_batch)} inputs)."
            )
        embeddings.extend(embedding.values for embedding in batch_embeddings)
    return embeddings


def _read_records(project_id: str) -> list[dict]:
    path = _project_file(project_id)
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as file:
        payload = json.load(file)
    return payload.get("records", [])


def add_code_chunks(project_id: str, chunks: list, metadata: list, ids: list):
    if not (len(chunks) == len(metadata) == len(ids)):
        raise ValueError("chunks, metadata, and ids must have the same length")

    embeddings = _embed_texts(chunks)
    path = _project_file(project_id)

    with STORE_LOCK:
        records_by_id = {record["id"]: record for record in _read_records(project_id)}
        for chunk_id, chunk, meta, embedding in zip(ids, chunks, metadata, embeddings):
            records_by_id[chunk_id] = {
                "id": chunk_id,
                "document": chunk,
                "metadata": meta,
                "embedding": embedding,
            }

        temporary_path = path.with_suffix(".tmp")
        with temporary_path.open("w", encoding="utf-8") as file:
            json.dump({"records": list(records_by_id.values())}, file)
        temporary_path.replace(path)


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    dot_product = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if not left_norm or not right_norm:
        return 0.0
    return dot_product / (left_norm * right_norm)


def query_codebase(project_id: str, query: str, n_results: int = 4):
    records = _read_records(project_id)
    if not records:
        return {"documents": [[]], "metadatas": [[]], "distances": [[]]}

    query_embedding = _embed_texts([query])[0]
    ranked_records = sorted(
        records,
        key=lambda record: _cosine_similarity(query_embedding, record["embedding"]),
        reverse=True,
    )[:n_results]

    return {
        "documents": [[record["document"] for record in ranked_records]],
        "metadatas": [[record["metadata"] for record in ranked_records]],
        "distances": [[
            1 - _cosine_similarity(query_embedding, record["embedding"])
            for record in ranked_records
        ]],
    }