import os
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from code_parser import chunk_file
from vector_store import add_code_chunks, query_codebase

app = FastAPI(title="Codebase RAG Microservice")

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

class IndexRequest(BaseModel):
    project_id: str
    repo_path: str

class QueryRequest(BaseModel):
    project_id: str
    query: str
    model: str = "qwen2.5-coder:7b"

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "Python RAG Engine"}

@app.post("/index-repo")
def index_repository(req: IndexRequest):
    if not os.path.exists(req.repo_path):
        raise HTTPException(status_code=400, detail="Repository path does not exist")

    all_chunks = []
    all_metadatas = []
    all_ids = []
    counter = 0

    # Scan repository ignoring common build/git directories
    ignored_dirs = {".git", "node_modules", "dist", "build", "venv", "__pycache__"}

    for root, dirs, files in os.walk(req.repo_path):
        dirs[:] = [d for d in dirs if d not in ignored_dirs]
        for file in files:
            if file.endswith((".js", ".jsx", ".ts", ".tsx", ".py")):
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, req.repo_path)
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        content = f.read()

                    docs = chunk_file(rel_path, content)
                    for doc in docs:
                        counter += 1
                        chunk_id = f"{req.project_id}_{counter}"
                        all_chunks.append(doc.page_content)
                        all_metadatas.append(doc.metadata)
                        all_ids.append(chunk_id)
                except Exception as e:
                    print(f"Skipping {rel_path}: {e}")

    if all_chunks:
        add_code_chunks(req.project_id, all_chunks, all_metadatas, all_ids)

    return {
        "success": True,
        "project_id": req.project_id,
        "total_chunks_indexed": len(all_chunks)
    }

@app.post("/query-codebase")
def query_code(req: QueryRequest):
    # 1. Retrieve top matching code snippets from ChromaDB
    search_results = query_codebase(req.project_id, req.query, n_results=4)
    
    retrieved_docs = search_results.get("documents", [[]])[0]
    retrieved_meta = search_results.get("metadatas", [[]])[0]

    context_str = ""
    citations = []
    for doc, meta in zip(retrieved_docs, retrieved_meta):
        file_path = meta.get("file_path", "unknown")
        citations.append(file_path)
        context_str += f"\n--- File: {file_path} ---\n{doc}\n"

    # 2. Formulate Prompt for Ollama Code Model
    prompt = f"""
You are an expert Code Intelligence AI. Answer the developer query based strictly on the provided codebase snippets.

Retrieved Codebase Context:
{context_str}

Developer Question:
{req.query}

Provide a concise, highly accurate response with relevant code examples if applicable.
"""

    # 3. Query Local Ollama Instance
    try:
        res = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json={
                "model": req.model,
                "prompt": prompt,
                "stream": False
            }
        )
        response_json = res.json()
        answer = response_json.get("response", "No response generated")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ollama execution failed: {str(e)}")

    return {
        "success": True,
        "answer": answer,
        "citations": list(set(citations))
    }