import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).with_name(".env"))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from code_parser import chunk_file
from vector_store import add_code_chunks, query_codebase, get_ai_client

app = FastAPI(title="Codebase RAG Microservice")

class IndexRequest(BaseModel):
    project_id: str
    repo_path: str

class QueryRequest(BaseModel):
    project_id: str
    query: str
    model: str = "gemini-2.5-flash"

class RefactorRequest(BaseModel):
    code_snippet: str
    instruction: str
    file_path: str = "snippet.js"
    model: str = "gemini-2.5-flash"

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "Python RAG Engine"}

@app.post("/index-repo")
def index_repository(req: IndexRequest):
    clean_path = os.path.normpath(req.repo_path)

    if not os.path.exists(clean_path):
        raise HTTPException(status_code=400, detail=f"Repository path does not exist: {clean_path}")

    ignored_dirs = {
        ".git", "node_modules", "dist", "build", "venv", ".venv", 
        "__pycache__", "chroma_db", ".vscode", ".idea", ".next", "coverage"
    }
    allowed_extensions = (".js", ".jsx", ".ts", ".tsx", ".py", ".html", ".css", ".json")

    counter = 0
    buffer_chunks = []
    buffer_meta = []
    buffer_ids = []
    total_indexed = 0

    for root, dirs, files in os.walk(clean_path):
        dirs[:] = [
            d for d in dirs
            if d not in ignored_dirs and not d.startswith("chroma_db")
        ]
        for file in files:
            if file.endswith(allowed_extensions) and not file.endswith("-lock.json"):
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, clean_path)
                try:
                    with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()

                    if not content.strip():
                        continue

                    docs = chunk_file(rel_path, content)
                    for doc in docs:
                        counter += 1
                        chunk_id = f"{req.project_id}_{counter}"
                        buffer_chunks.append(doc.page_content)
                        buffer_meta.append(doc.metadata)
                        buffer_ids.append(chunk_id)

                        if len(buffer_chunks) >= 50:
                            try:
                                print(
                                    f"Indexing chunks {counter - len(buffer_chunks) + 1}-{counter}",
                                    flush=True,
                                )
                                add_code_chunks(req.project_id, buffer_chunks, buffer_meta, buffer_ids)
                            except Exception as e:
                                raise HTTPException(
                                    status_code=502,
                                    detail=f"Embedding or ChromaDB storage failed: {e}",
                                ) from e
                            total_indexed += len(buffer_chunks)
                            buffer_chunks, buffer_meta, buffer_ids = [], [], []

                except HTTPException:
                    raise
                except Exception as e:
                    print(f"Skipping {rel_path}: {e}")

    if buffer_chunks:
        try:
            add_code_chunks(req.project_id, buffer_chunks, buffer_meta, buffer_ids)
        except Exception as e:
            raise HTTPException(
                status_code=502,
                detail=f"Embedding or ChromaDB storage failed: {e}",
            ) from e
        total_indexed += len(buffer_chunks)

    if total_indexed == 0:
        raise HTTPException(status_code=400, detail="No indexable code files found.")

    return {
        "success": True,
        "project_id": req.project_id,
        "total_chunks_indexed": total_indexed
    }

@app.post("/query-codebase")
def query_code(req: QueryRequest):
    try:
        search_results = query_codebase(req.project_id, req.query, n_results=4)
        retrieved_docs = search_results.get("documents", [[]])[0]
        retrieved_meta = search_results.get("metadatas", [[]])[0]

        context_str = ""
        citations = []
        for doc, meta in zip(retrieved_docs, retrieved_meta):
            file_path = meta.get("file_path", "unknown")
            citations.append(file_path)
            context_str += f"\n--- File: {file_path} ---\n{doc}\n"
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ChromaDB retrieval error: {str(e)}")

    prompt_text = f"""
You are an expert Code Intelligence AI. Answer the developer query based strictly on the provided codebase snippets.

Retrieved Codebase Context:
{context_str}

Developer Question:
{req.query}
"""

    try:
        # Guarantee valid Gemini model name even if frontend sends Ollama string
        target_model = req.model if "gemini" in req.model.lower() else "gemini-2.5-flash"
        client_instance = get_ai_client()
        response = client_instance.models.generate_content(
            model=target_model,
            contents=prompt_text,
        )
        answer = response.text
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gemini execution failed: {str(e)}")

    return {
        "success": True,
        "answer": answer,
        "citations": list(set(citations))
    }

@app.post("/refactor-code")
def refactor_code(req: RefactorRequest):
    prompt_text = f"""
You are an expert Code Refactoring Engine. Transform the following code based strictly on the instruction.
Return ONLY the raw executable code without markdown formatting, introductory text, or explanations.

Target File Path: {req.file_path}
Instruction: {req.instruction}

Original Code:
{req.code_snippet}
"""
    try:
        target_model = req.model if "gemini" in req.model.lower() else "gemini-2.5-flash"
        client_instance = get_ai_client()
        response = client_instance.models.generate_content(
            model=target_model,
            contents=prompt_text,
        )
        refactored_code = response.text.strip()
        
        if refactored_code.startswith("```"):
            lines = refactored_code.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            refactored_code = "\n".join(lines).strip()

        return {
            "success": True,
            "refactored_code": refactored_code
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Refactoring failed: {str(e)}")