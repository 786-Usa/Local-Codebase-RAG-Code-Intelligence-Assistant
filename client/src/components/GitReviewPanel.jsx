import React, { useState } from "react";
import { reviewGitDiff } from "../services/api";
import { GitPullRequest, Loader2, ShieldAlert } from "lucide-react";

export default function GitReviewPanel({ repoPath }) {
  const [review, setReview] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleRunReview = async () => {
    if (!repoPath) return;
    setIsLoading(true);
    try {
      const res = await reviewGitDiff(repoPath);
      if (res.success) setReview(res.review);
    } catch (err) {
      setReview("PR Review failed: " + (err.response?.data?.detail || err.message));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="h-full w-full flex flex-col bg-gray-950 p-4">
      <div className="p-3 bg-gray-900 border border-gray-800 rounded-lg flex items-center justify-between mb-4">
        <div className="flex items-center gap-2 text-indigo-400 text-xs font-semibold">
          <GitPullRequest className="w-4 h-4 text-emerald-400" />
          <span>Automated Git Diff & PR Security Review</span>
        </div>
        <button
          onClick={handleRunReview}
          disabled={isLoading || !repoPath}
          className="px-4 py-1.5 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white rounded text-xs font-semibold flex items-center gap-1.5 transition-colors"
        >
          {isLoading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <ShieldAlert className="w-3.5 h-3.5" />}
          Analyze Git Diff
        </button>
      </div>

      <div className="flex-1 bg-gray-900 border border-gray-800 rounded-lg p-4 overflow-y-auto font-mono text-xs leading-relaxed text-gray-200 whitespace-pre-wrap">
        {isLoading ? (
          <div className="flex items-center gap-2 text-gray-400">
            <Loader2 className="w-4 h-4 animate-spin text-indigo-500" />
            <span>Scanning Git working tree diff with Gemini 3.6-flash...</span>
          </div>
        ) : review ? (
          review
        ) : (
          <p className="text-gray-500 italic">
            Click "Analyze Git Diff" to generate an automated PR review of uncommitted or recent changes in your repository.
          </p>
        )}
      </div>
    </div>
  );
}