import React, { useState } from "react";
import Editor from "@monaco-editor/react";
import {
  fetchFileTree,
  fetchFileContent,
  indexRepository,
  queryCodebase,
} from "./services/api";
import FileTree from "./components/FileTree";
import DependencyGraph from "./components/DependencyGraph";
import RefactorPanel from "./components/RefactorPanel";
import GitReviewPanel from "./components/GitReviewPanel";
import {
  Code2,
  Search,
  Database,
  Terminal,
  Loader2,
  Folder,
  Network,
  FileCode,
  Sparkles,
  GitPullRequest,
} from "lucide-react";

export default function App() {
  const [repoPath, setRepoPath] = useState("");
  const [projectId, setProjectId] = useState("my_project");
  const [fileTree, setFileTree] = useState(null);
  const [activeFile, setActiveFile] = useState(null);
  const [fileContent, setFileContent] = useState(
    "// Select a file from the workspace tree to view code",
  );

  // View tab state: 'editor' | 'graph' | 'refactor' | 'review'
  const [activeTab, setActiveTab] = useState("editor");

  const [query, setQuery] = useState("");
  const [queryResult, setQueryResult] = useState("");
  const [citations, setCitations] = useState([]);

  const [isIndexing, setIsIndexing] = useState(false);
  const [isQuerying, setIsQuerying] = useState(false);
  const [statusMsg, setStatusMsg] = useState("");

  const handleLoadRepo = async () => {
    if (!repoPath) return;
    try {
      const res = await fetchFileTree(repoPath);
      if (res.success) setFileTree(res.data);
    } catch (err) {
      setStatusMsg("Failed to load file tree: " + err.message);
    }
  };

  const handleSelectFile = async (filePath) => {
    setActiveFile(filePath);
    setActiveTab("editor"); // Switch to editor view when selecting a file
    try {
      const res = await fetchFileContent(filePath);
      if (res.success) setFileContent(res.data.content);
    } catch (err) {
      setFileContent("// Error loading file content");
    }
  };

  const handleIndexRepo = async () => {
    if (!repoPath || !projectId) return;
    setIsIndexing(true);
    setStatusMsg("Indexing codebase into JSON vector store...");
    try {
      const res = await indexRepository(projectId, repoPath);
      if (res.success) {
        setStatusMsg(
          `Successfully indexed ${res.total_chunks_indexed} AST code chunks!`,
        );
      }
    } catch (err) {
      setStatusMsg("Indexing failed: " + err.message);
    } finally {
      setIsIndexing(false);
    }
  };

  const handleQuery = async (e) => {
    e.preventDefault();
    if (!query || !projectId) return;
    setIsQuerying(true);
    try {
      const res = await queryCodebase(projectId, query);
      if (res.success) {
        setQueryResult(res.answer);
        setCitations(res.citations || []);
      }
    } catch (err) {
      setQueryResult("Query execution failed: " + err.message);
    } finally {
      setIsQuerying(false);
    }
  };

  return (
    <div className="h-screen w-screen bg-gray-950 text-gray-100 flex flex-col font-sans overflow-hidden">
      {/* Header Bar */}
      <header className="h-14 border-b border-gray-800 bg-gray-900 px-4 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-2 text-indigo-400 font-bold text-lg">
          <Code2 className="w-6 h-6" />
          <h1>Local Codebase RAG & Intelligence Assistant</h1>
        </div>

        <div className="flex items-center gap-3">
          <input
            type="text"
            placeholder="Project ID (e.g. my_project)"
            value={projectId}
            onChange={(e) => setProjectId(e.target.value)}
            className="px-3 py-1.5 bg-gray-800 border border-gray-700 rounded text-xs text-gray-200 outline-none focus:border-indigo-500 w-40"
          />
          <input
            type="text"
            placeholder="Local Repository Path (e.g. D:\path\to\repo)"
            value={repoPath}
            onChange={(e) => setRepoPath(e.target.value)}
            className="px-3 py-1.5 bg-gray-800 border border-gray-700 rounded text-xs text-gray-200 outline-none focus:border-indigo-500 w-72"
          />
          <button
            onClick={handleLoadRepo}
            className="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 border border-gray-700 rounded text-xs font-semibold flex items-center gap-1.5 transition-colors"
          >
            <Folder className="w-3.5 h-3.5 text-amber-400" /> Load Tree
          </button>
          <button
            onClick={handleIndexRepo}
            disabled={isIndexing}
            className="px-3.5 py-1.5 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 rounded text-xs font-semibold flex items-center gap-1.5 transition-colors shadow-sm"
          >
            {isIndexing ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <Database className="w-3.5 h-3.5" />
            )}
            Index Codebase
          </button>
        </div>
      </header>

      {/* Main Workspace Layout */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Sidebar: Workspace File Tree */}
        <aside className="w-64 border-r border-gray-800 bg-gray-900/50 p-3 flex flex-col shrink-0">
          <h2 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-3">
            Workspace Files
          </h2>
          <div className="flex-1 overflow-y-auto">
            {fileTree ? (
              <FileTree item={fileTree} onSelectFile={handleSelectFile} />
            ) : (
              <p className="text-xs text-gray-500 italic">
                Enter a repository path and click "Load Tree".
              </p>
            )}
          </div>
          {statusMsg && (
            <div className="mt-2 p-2 bg-gray-800 border border-gray-700 text-[11px] text-indigo-300 rounded">
              {statusMsg}
            </div>
          )}
        </aside>

        {/* Center Panel: Editor OR AST Dependency Graph OR Refactor Diff OR PR Review */}
        <main className="flex-1 flex flex-col border-r border-gray-800 overflow-hidden">
          {/* View Mode Toggle Header */}
          <div className="h-9 bg-gray-900 px-4 border-b border-gray-800 flex items-center justify-between text-xs text-gray-400 shrink-0">
            <div className="flex items-center gap-2">
              <button
                onClick={() => setActiveTab("editor")}
                className={`flex items-center gap-1.5 px-3 py-1 rounded transition-colors ${
                  activeTab === "editor"
                    ? "bg-gray-800 text-indigo-400 font-semibold"
                    : "hover:bg-gray-800/50 text-gray-400"
                }`}
              >
                <FileCode className="w-3.5 h-3.5" /> Code View
              </button>
              <button
                onClick={() => setActiveTab("graph")}
                className={`flex items-center gap-1.5 px-3 py-1 rounded transition-colors ${
                  activeTab === "graph"
                    ? "bg-gray-800 text-indigo-400 font-semibold"
                    : "hover:bg-gray-800/50 text-gray-400"
                }`}
              >
                <Network className="w-3.5 h-3.5" /> AST Dependency Graph
              </button>
              <button
                onClick={() => setActiveTab("refactor")}
                className={`flex items-center gap-1.5 px-3 py-1 rounded transition-colors ${
                  activeTab === "refactor"
                    ? "bg-gray-800 text-amber-400 font-semibold"
                    : "hover:bg-gray-800/50 text-gray-400"
                }`}
              >
                <Sparkles className="w-3.5 h-3.5 text-amber-400" /> Refactor Diff
              </button>
              <button
                onClick={() => setActiveTab("review")}
                className={`flex items-center gap-1.5 px-3 py-1 rounded transition-colors ${
                  activeTab === "review"
                    ? "bg-gray-800 text-emerald-400 font-semibold"
                    : "hover:bg-gray-800/50 text-gray-400"
                }`}
              >
                <GitPullRequest className="w-3.5 h-3.5 text-emerald-400" /> PR Review
              </button>
            </div>
            <span className="text-[11px] text-gray-500 truncate max-w-xs">
              {activeTab === "graph"
                ? `Graph view: ${projectId}`
                : activeTab === "review"
                ? `PR Review: ${repoPath || "No repo specified"}`
                : activeFile || "No file selected"}
            </span>
          </div>

          {/* View Body */}
          <div className="flex-1 bg-gray-950 relative overflow-hidden">
            {activeTab === "editor" ? (
              <Editor
                height="100%"
                theme="vs-dark"
                path={activeFile || "file.js"}
                value={fileContent}
                options={{
                  readOnly: true,
                  fontSize: 13,
                  minimap: { enabled: false },
                  scrollBeyondLastLine: false,
                }}
              />
            ) : activeTab === "graph" ? (
              <div className="h-full w-full p-2">
                <DependencyGraph projectId={projectId} />
              </div>
            ) : activeTab === "refactor" ? (
              <RefactorPanel activeFile={activeFile} fileContent={fileContent} />
            ) : (
              <GitReviewPanel repoPath={repoPath} />
            )}
          </div>
        </main>

        {/* Right Sidebar: AI Query & Code Intelligence Assistant */}
        <aside className="w-96 bg-gray-900/50 flex flex-col shrink-0 overflow-hidden">
          <div className="p-3 border-b border-gray-800 font-semibold text-xs text-indigo-400 flex items-center gap-2">
            <Terminal className="w-4 h-4" />
            <span>RAG Code Intelligence Query</span>
          </div>

          {/* AI Response Output Area */}
          <div className="flex-1 p-4 overflow-y-auto space-y-4">
            {isQuerying ? (
              <div className="flex items-center gap-2 text-xs text-gray-400">
                <Loader2 className="w-4 h-4 animate-spin text-indigo-500" />
                <span>
                  Searching vector store & executing Gemini inference...
                </span>
              </div>
            ) : queryResult ? (
              <div className="space-y-3">
                <div className="p-3 bg-gray-900 border border-gray-800 rounded-lg text-xs leading-relaxed text-gray-200 whitespace-pre-wrap font-mono">
                  {queryResult}
                </div>
                {citations.length > 0 && (
                  <div>
                    <h4 className="text-[11px] font-bold text-gray-400 uppercase tracking-wider mb-1">
                      Citations
                    </h4>
                    <div className="space-y-1">
                      {citations.map((c, i) => (
                        <div
                          key={i}
                          className="text-[11px] text-indigo-400 bg-indigo-950/40 border border-indigo-900/50 px-2 py-0.5 rounded truncate"
                        >
                          {c}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <p className="text-xs text-gray-500 italic">
                Ask a natural language query like "Where is get_ai_client defined?" or "Explain the data flow in main.py".
              </p>
            )}
          </div>

          {/* Query Input Box */}
          <form
            onSubmit={handleQuery}
            className="p-3 border-t border-gray-800 bg-gray-900 flex gap-2"
          >
            <input
              type="text"
              placeholder="Ask code intelligence..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="flex-1 px-3 py-2 bg-gray-800 border border-gray-700 rounded text-xs text-gray-200 outline-none focus:border-indigo-500"
            />
            <button
              type="submit"
              disabled={isQuerying}
              className="px-3 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white rounded text-xs font-semibold flex items-center transition-colors"
            >
              <Search className="w-4 h-4" />
            </button>
          </form>
        </aside>
      </div>
    </div>
  );
}