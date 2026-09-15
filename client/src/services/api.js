import axios from 'axios';

const API_BASE_URL = 'http://localhost:5000/api/codebase';

export const fetchFileTree = async (repoPath) => {
  const res = await axios.get(`${API_BASE_URL}/tree`, { params: { repoPath } });
  return res.data;
};

export const fetchFileContent = async (filePath) => {
  const res = await axios.get(`${API_BASE_URL}/file-content`, { params: { filePath } });
  return res.data;
};

export const indexRepository = async (projectId, repoPath) => {
  const res = await axios.post(`${API_BASE_URL}/index`, { projectId, repoPath });
  return res.data;
};

export const queryCodebase = async (projectId, query, model = 'qwen2.5-coder:7b') => {
  const res = await axios.post(`${API_BASE_URL}/query`, { projectId, query, model });
  return res.data;
};