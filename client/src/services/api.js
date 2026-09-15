import axios from "axios";

const API_BASE_URL = "http://localhost:5000/api/codebase";

export const fetchFileTree = async (repoPath) => {
  const res = await axios.get(`${API_BASE_URL}/tree`, { params: { repoPath } });
  return res.data;
};

export const fetchFileContent = async (filePath) => {
  const res = await axios.get(`${API_BASE_URL}/file-content`, {
    params: { filePath },
  });
  return res.data;
};

export const indexRepository = async (projectId, repoPath) => {
  const res = await axios.post(`${API_BASE_URL}/index`, {
    projectId,
    repoPath,
  });
  return res.data;
};

export const queryCodebase = async (
  projectId,
  query,
  model = "gemini-3.6-flash",
) => {
  const res = await axios.post(`${API_BASE_URL}/query`, {
    projectId,
    query,
    model,
  });
  return res.data;
};

export const refactorCode = async (codeSnippet, instruction, filePath, model = "gemini-3.6-flash") => {
  const response = await axios.post(`${API_BASE_URL}/refactor-code`, {
    code_snippet: codeSnippet,
    instruction,
    file_path: filePath,
    model,
  });
  return response.data;
};

// Append to client/src/services/api.js:
// Append or verify in client/src/services/api.js:

export const reviewGitDiff = async (repoPath, model = "gemini-3.6-flash") => {
  const response = await axios.post(`${API_BASE_URL}/git-diff-review`, {
    repo_path: repoPath,
    model,
  });
  return response.data;
};