# Local Codebase RAG & Code Intelligence Assistant

A lightweight, high-performance local RAG (Retrieval-Augmented Generation) microservice and interactive developer workspace built to index codebases, analyze cross-file AST dependencies, generate instruction-based code refactorings, and perform automated Git-diff PR security reviews using **Google Gemini 3.6-flash**.

---

## 🌟 Key Features

* **Atomic Pure-Python Vector Store:** Replaces volatile native C++/Rust vector databases with a thread-safe, lightweight JSON store utilizing cosine similarity scoring to guarantee zero process crashes on Windows environments.
* **AST-Aware Code Chunking:** Extracts structural metadata (exported functions, class definitions, and imported module targets) using Python's native `ast` module and regex parsers for JavaScript/TypeScript to contextually enrich RAG prompts.
* **Visual AST Dependency Graph:** Interactive, node-based visual diagram of cross-file module imports and symbol relations powered by `@xyflow/react`.
* **Side-by-Side Code Refactoring:** Split-diff editor using `@monaco-editor/react` to execute natural language refactoring instructions directly on selected files.
* **Automated Git Diff & PR Security Review:** Subprocess execution of `git diff` outputs analyzed by Gemini to generate structured code reviews, security vulnerability checks, and optimization suggestions.
* **Gemini Cloud Intelligence:** Integrates `gemini-embedding-001` (768-dim) for high-dimensional vector embeddings and `gemini-3.6-flash` for rapid context inference.

---

## 🏗️ Architecture Overview

```
 ┌──────────────────────────────────────────────────────────┐
 │               React 18 SPA Frontend                      │
 │     (Monaco Editor + React Flow + Lucide + Tailwind)     │
 └────────────────────────────┬─────────────────────────────┘
                              │ HTTP (Port 5000)
                              ▼
 ┌──────────────────────────────────────────────────────────┐
 │              Express.js API Gateway Proxy                │
 └────────────────────────────┬─────────────────────────────┘
                              │ HTTP (Port 8000)
                              ▼
 ┌──────────────────────────────────────────────────────────┐
 │                Python FastAPI Microservice               │
 │    (AST Code Parsing + Atomic Vector Store + Gemini API)  │
 └──────────────────────────────────────────────────────────┘

```

---

## 📁 Repository Structure

```text
code-intelligence-assistant/
├── client/                     # React 18 SPA Frontend
│   ├── src/
│   │   ├── components/
│   │   │   ├── DependencyGraph.jsx   # Visual AST Graph (@xyflow/react)
│   │   │   ├── FileTree.jsx          # Workspace file explorer tree
│   │   │   ├── GitReviewPanel.jsx    # PR Security Review Panel
│   │   │   └── RefactorPanel.jsx     # Side-by-side Monaco Diff Editor
│   │   ├── services/
│   │   │   └── api.js            # Axios HTTP client endpoints
│   │   ├── App.jsx               # Workspace layout with 4-tab switcher
│   │   └── main.jsx
│   └── package.json
├── server/                     # Express.js API Gateway
│   ├── controllers/
│   │   └── codebaseController.js # Proxy logic for FastAPI microservice
│   ├── routes/
│   │   └── codebaseRoutes.js     # Gateway route definitions
│   └── index.js                  # Gateway server entry point (Port 5000)
└── rag-service/                # Python RAG Microservice
    ├── vector_data/              # Local JSON vector records storage
    ├── code_parser.py            # AST symbol & import metadata parser
    ├── vector_store.py           # Atomic cosine-similarity vector store
    ├── main.py                   # FastAPI application routes (Port 8000)
    └── requirements.txt

```

---

## 🚀 Getting Started

### Prerequisites

* **Node.js**: v18.x or higher
* **Python**: v3.10 or higher
* **Google Gemini API Key**: Obtainable from Google AI Studio.

---

### Setup Instructions

#### 1. Python RAG Microservice Setup

```powershell
cd rag-service

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\activate

# Install required dependencies
pip install -r requirements.txt

# Create environment configuration file
New-Item -ItemType File -Name .env

```

Add your Gemini API Key to `rag-service/.env`:

```env
GEMINI_API_KEY=your_gemini_api_key_here

```

Start the FastAPI microservice on port `8000`:

```powershell
.\venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000

```

#### 2. Express Gateway Server Setup

```powershell
cd ../server

# Install dependencies
npm install

# Start Express server on port 5000
npm start

```

#### 3. React SPA Frontend Setup

```powershell
cd ../client

# Install dependencies
npm install

# Start Vite development server
npm run dev

```

---

## 📡 API Reference

### Microservice Endpoints (`http://localhost:8000`)

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/health` | Health check endpoint returning service status |
| `POST` | `/index-repo` | Scans workspace, parses AST metadata, and builds vector index |
| `POST` | `/query-codebase` | Performs semantic search & runs query inference via `gemini-3.6-flash` |
| `POST` | `/refactor-code` | Transforms input code based on refactoring instructions |
| `GET` | `/dependency-graph/{project_id}` | Returns AST nodes and edge relations for visualization |
| `POST` | `/git-diff-review` | Executes `git diff` and generates automated PR security review |

---

## 🧪 Smoke Testing

Run the following PowerShell command to test codebase vector indexing:

```powershell
$body = @{ 
    project_id = 'test_project'; 
    repo_path = 'D:\path\to\your\repository' 
} | ConvertTo-Json

Invoke-RestMethod -Uri http://localhost:8000/index-repo -Method Post -ContentType 'application/json' -Body $body

```

Run a natural language code intelligence query:

```powershell
$body = @{ 
    project_id = 'test_project'; 
    query = 'Where are the API routes configured?'; 
    model = 'gemini-3.6-flash' 
} | ConvertTo-Json

Invoke-RestMethod -Uri http://localhost:8000/query-codebase -Method Post -ContentType 'application/json' -Body $body

```

---

## 📜 License

This project is open-source under the MIT License.