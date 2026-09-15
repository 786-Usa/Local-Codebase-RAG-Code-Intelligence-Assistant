import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from code_parser import chunk_file
from vector_store import add_code_chunks, get_ai_client, query_codebase

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

app = FastAPI(title="Codebase RAG Microservice")


class IndexRequest(BaseModel):
    project_id: str
    repo_path: str


class QueryRequest(BaseModel):
    project_id: str
    query: str
    model: str = "gemini-3.6-flash"


class RefactorRequest(BaseModel):
    code_snippet: str
    instruction: str
    file_path: str = "snippet.js"
    model: str = "gemini-3.6-flash"


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "Python RAG Engine"}


@app.post("/index-repo")
def index_repository(req: IndexRequest):
    clean_path = os.path.normpath(req.repo_path)

    if not os.path.exists(clean_path):
        raise HTTPException(
            status_code=400, detail=f"Repository path does not exist: {clean_path}"
        )

    all_chunks = []
    all_metadatas = []
    all_ids = []
    counter = 0

    # Extended ignored list to prevent memory bloat & vector directory recursion
    ignored_dirs = {
        ".git",
        "node_modules",
        "dist",
        "build",
        "venv",
        ".venv",
        "__pycache__",
        "vector_data",
        "chroma_db",
        "chroma_db_backup",
        ".vscode",
        ".idea",
        ".next",
        "coverage",
    }
    allowed_extensions = (".js", ".jsx", ".ts", ".tsx", ".py", ".html", ".css", ".json")

    for root, dirs, files in os.walk(clean_path):
        dirs[:] = [d for d in dirs if d not in ignored_dirs]
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
                        all_chunks.append(doc.page_content)
                        all_metadatas.append(doc.metadata)
                        all_ids.append(chunk_id)
                except Exception as e:
                    print(f"Skipping {rel_path}: {e}")

    if not all_chunks:
        raise HTTPException(status_code=400, detail="No indexable code files found.")

    add_code_chunks(req.project_id, all_chunks, all_metadatas, all_ids)

    return {
        "success": True,
        "project_id": req.project_id,
        "total_chunks_indexed": len(all_chunks),
    }


@app.post("/query-codebase")
def query_code(req: QueryRequest):
    try:
        search_results = query_codebase(req.project_id, req.query, n_results=4)
        retrieved_docs = search_results.get("documents", [[]])[0]
        retrieved_meta = search_results.get("metadatas", [[]])[0]
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Vector search failed: {e}") from e

    citations = [meta.get("file_path", "unknown") for meta in retrieved_meta]

    # Inject AST symbols and imported modules into Gemini prompt context
    context_blocks = []
    for doc, meta in zip(retrieved_docs, retrieved_meta):
        file_path = meta.get("file_path", "unknown")
        symbols = ", ".join(meta.get("symbols", [])) or "None"
        imports = ", ".join(meta.get("imports", [])) or "None"

        block = (
            f"\n--- File: {file_path} ---\n"
            f"Defined Symbols: {symbols}\n"
            f"Imported Modules: {imports}\n"
            f"Content:\n{doc}\n"
        )
        context_blocks.append(block)

    context_str = "".join(context_blocks)

    prompt = f"""
You are an expert Code Intelligence AI. Answer the developer query based strictly on the provided codebase snippets.

Retrieved Codebase Context:
{context_str}

Developer Question:
{req.query}

Provide a concise, highly accurate response with relevant code examples if applicable.
"""

    try:
        target_model = (
            req.model
            if req.model and req.model.lower().startswith("gemini-")
            else "gemini-3.6-flash"
        )
        response = get_ai_client().models.generate_content(
            model=target_model,
            contents=prompt,
        )
        answer = response.text or "No response generated"
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Gemini execution failed: {e}") from e

    return {
        "success": True,
        "answer": answer,
        "citations": list(set(citations)),
    }


@app.post("/refactor-code")
def refactor_code(req: RefactorRequest):
    prompt = f"""
You are an expert Code Refactoring Engine. Transform the following code based strictly on the instruction.
Return ONLY the raw executable code without markdown formatting, introductory text, or explanations.

Target File Path: {req.file_path}
Instruction: {req.instruction}

Original Code:
{req.code_snippet}
"""
    try:
        target_model = (
            req.model
            if req.model and req.model.lower().startswith("gemini-")
            else "gemini-3.6-flash"
        )
        response = get_ai_client().models.generate_content(
            model=target_model,
            contents=prompt,
        )
        refactored_code = (response.text or "").strip()

        if refactored_code.startswith("```"):
            lines = refactored_code.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            refactored_code = "\n".join(lines).strip()

        return {"success": True, "refactored_code": refactored_code}
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Refactoring failed: {e}") from e

# Append to rag-service/main.py:

@app.get("/dependency-graph/{project_id}")
def get_dependency_graph(project_id: str):
    from vector_store import _read
    records = _read(project_id)
    
    if not records:
        return {"nodes": [], "edges": []}
        
    nodes = []
    edges = []
    seen_files = set()
    edge_set = set()

    for record in records:
        meta = record.get("metadata", {})
        file_path = meta.get("file_path", "")
        symbols = meta.get("symbols", [])
        imports = meta.get("imports", [])

        if file_path and file_path not in seen_files:
            seen_files.add(file_path)
            nodes.append({
                "id": file_path,
                "label": file_path,
                "symbols": symbols,
                "extension": meta.get("extension", "")
            })

        for imp in imports:
            # Check if imported module matches any indexed relative file path
            for target_file in seen_files:
                if imp in target_file or target_file.endswith(f"{imp}.js") or target_file.endswith(f"{imp}.py"):
                    edge_id = f"{file_path}->{target_file}"
                    if edge_id not in edge_set:
                        edge_set.add(edge_id)
                        edges.append({
                            "id": edge_id,
                            "source": file_path,
                            "target": target_file
                        })

    return {"nodes": nodes, "edges": edges}