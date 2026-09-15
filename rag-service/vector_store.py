import os
import chromadb
from chromadb.utils import embedding_functions

# Persistent storage directory for code vector databases
PERSIST_DIRECTORY = os.path.join(os.path.dirname(__file__), "chroma_db")

client = chromadb.PersistentClient(path=PERSIST_DIRECTORY)

# Use default sentence-transformer embedding function
embedding_fn = embedding_functions.DefaultEmbeddingFunction()

def get_collection(project_id: str):
    return client.get_or_create_collection(
        name=f"repo_{project_id}",
        embedding_function=embedding_fn
    )

def add_code_chunks(project_id: str, chunks: list, metadata: list, ids: list):
    collection = get_collection(project_id)
    collection.add(
        documents=chunks,
        metadatas=metadata,
        ids=ids
    )

def query_codebase(project_id: str, query: str, n_results: int = 4):
    collection = get_collection(project_id)
    results = collection.query(
        query_texts=[query],
        n_results=n_results
    )
    return results