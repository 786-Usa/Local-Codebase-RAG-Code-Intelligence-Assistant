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

_ai_client = None


def get_ai_client():
    global _ai_client
    if _ai_client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not set in environment or .env file.")
        _ai_client = genai.Client(api_key=api_key)
    return _ai_client

STORE_DIRECTORY = Path(__file__).with_name("vector_data")
STORE_DIRECTORY.mkdir(exist_ok=True)
STORE_LOCK = Lock()


def _project_path(project_id: str) -> Path:
    safe_id = re.sub(r"[^a-zA-Z0-9_.-]", "_", project_id)
    if not safe_id:
        raise ValueError("project_id is required")
    return STORE_DIRECTORY / f"{safe_id}.json"


def _embed(texts: list[str]) -> list[list[float]]:
    embeddings = []
    client_instance = get_ai_client()
    for start in range(0, len(texts), 8):
        batch = texts[start:start + 8]
        response = client_instance.models.embed_content(
            model="gemini-embedding-001",
            contents=batch,
            config=types.EmbedContentConfig(output_dimensionality=768),
        )
        batch_embeddings = response.embeddings or []
        if len(batch_embeddings) != len(batch):
            raise RuntimeError("Gemini returned an invalid embedding count")
        embeddings.extend(item.values for item in batch_embeddings)
    return embeddings


def _read(project_id: str) -> list[dict]:
    path = _project_path(project_id)
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as file:
        return json.load(file).get("records", [])


def add_code_chunks(project_id: str, chunks: list, metadata: list, ids: list):
    if not len(chunks) == len(metadata) == len(ids):
        raise ValueError("chunks, metadata, and ids must have the same length")
    embeddings = _embed(chunks)
    with STORE_LOCK:
        records = {record["id"]: record for record in _read(project_id)}
        for chunk_id, chunk, meta, embedding in zip(ids, chunks, metadata, embeddings):
            records[chunk_id] = {
                "id": chunk_id,
                "document": chunk,
                "metadata": meta,
                "embedding": embedding,
            }
        path = _project_path(project_id)
        temporary_path = path.with_suffix(".tmp")
        with temporary_path.open("w", encoding="utf-8") as file:
            json.dump({"records": list(records.values())}, file)
        temporary_path.replace(path)


def _similarity(left: list[float], right: list[float]) -> float:
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    return dot / (left_norm * right_norm) if left_norm and right_norm else 0.0


def query_codebase(project_id: str, query: str, n_results: int = 4):
    records = _read(project_id)
    if not records:
        return {"documents": [[]], "metadatas": [[]]}
    query_embedding = _embed([query])[0]
    records.sort(
        key=lambda record: _similarity(query_embedding, record["embedding"]),
        reverse=True,
    )
    selected = records[:n_results]
    return {
        "documents": [[record["document"] for record in selected]],
        "metadatas": [[record["metadata"] for record in selected]],
    }