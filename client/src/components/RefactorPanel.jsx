import React, { useState } from "react";
import { DiffEditor } from "@monaco-editor/react";
import { refactorCode } from "../services/api";
import { Sparkles, Loader2, Check } from "lucide-react";

export default function RefactorPanel({ activeFile, fileContent }) {
  const [instruction, setInstruction] = useState("");
  const [refactoredCode, setRefactoredCode] = useState(fileContent);
  const [isLoading, setIsLoading] = useState(false);
  const [status, setStatus] = useState("");

  const handleRefactor = async (e) => {
    e.preventDefault();
    if (!instruction.trim() || !fileContent) return;

    setIsLoading(true);
    setStatus("Executing Gemini 3.6-flash refactoring...");

    try {
      const res = await refactorCode(fileContent, instruction, activeFile || "snippet.js");
      if (res.success) {
        setRefactoredCode(res.refactored_code);
        setStatus("Refactoring complete!");
      }
    } catch (err) {
      setStatus("Refactoring failed: " + (err.response?.data?.detail || err.message));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="h-full w-full flex flex-col bg-gray-950">
      {/* Refactor Instruction Bar */}
      <form onSubmit={handleRefactor} className="p-3 bg-gray-900 border-b border-gray-800 flex items-center gap-3 shrink-0">
        <input
          type="text"
          placeholder="Refactoring instruction (e.g., 'Convert to async/await', 'Add TypeScript types'...)"
          value={instruction}
          onChange={(e) => setInstruction(e.target.value)}
          className="flex-1 px-3 py-1.5 bg-gray-800 border border-gray-700 rounded text-xs text-gray-200 outline-none focus:border-indigo-500"
        />
        <button
          type="submit"
          disabled={isLoading || !instruction.trim()}
          className="px-4 py-1.5 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white rounded text-xs font-semibold flex items-center gap-1.5 transition-colors shrink-0"
        >
          {isLoading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5" />}
          Run Refactor
        </button>
      </form>

      {/* Diff View Header */}
      <div className="h-7 bg-gray-900/80 px-4 border-b border-gray-800/80 flex items-center justify-between text-[11px] text-gray-400 shrink-0">
        <span>Original Code (Left) vs. Refactored Code (Right)</span>
        {status && <span className="text-indigo-400 font-medium">{status}</span>}
      </div>

      {/* Side-by-Side Diff Monaco Editor */}
      <div className="flex-1">
        <DiffEditor
          height="100%"
          theme="vs-dark"
          original={fileContent}
          modified={refactoredCode}
          language={activeFile?.endsWith(".py") ? "python" : "javascript"}
          options={{
            readOnly: true,
            fontSize: 13,
            minimap: { enabled: false },
            originalEditable: false,
          }}
        />
      </div>
    </div>
  );
}