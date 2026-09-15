import axios from 'axios';
import fs from 'fs';
import { getDirectoryTree } from '../utils/fileScanner.js';

const PYTHON_SERVICE = process.env.PYTHON_RAG_SERVICE_URL || 'http://localhost:8000';

// GET /api/codebase/tree?repoPath=D:\path\to\repo
export const getFileTree = async (req, res) => {
  try {
    const { repoPath } = req.query;
    if (!repoPath || !fs.existsSync(repoPath)) {
      return res.status(400).json({ success: false, message: 'Invalid repository path' });
    }

    const tree = getDirectoryTree(repoPath);
    res.status(200).json({ success: true, data: tree });
  } catch (error) {
    res.status(500).json({ success: false, message: error.message });
  }
};

// GET /api/codebase/file-content?filePath=...
export const getFileContent = async (req, res) => {
  try {
    const { filePath } = req.query;
    if (!filePath || !fs.existsSync(filePath)) {
      return res.status(400).json({ success: false, message: 'File not found' });
    }

    const content = fs.readFileSync(filePath, 'utf-8');
    res.status(200).json({ success: true, data: { filePath, content } });
  } catch (error) {
    res.status(500).json({ success: false, message: error.message });
  }
};

// POST /api/codebase/index
export const indexRepository = async (req, res) => {
  try {
    const { projectId, repoPath } = req.body;

    const response = await axios.post(`${PYTHON_SERVICE}/index-repo`, {
      project_id: projectId,
      repo_path: repoPath
    });

    res.status(200).json(response.data);
  } catch (error) {
    res.status(500).json({
      success: false,
      message: error.response?.data?.detail || error.message
    });
  }
};

// POST /api/codebase/query
export const queryCodebase = async (req, res) => {
  try {
    const { projectId, query, model } = req.body;

    const response = await axios.post(`${PYTHON_SERVICE}/query-codebase`, {
      project_id: projectId,
      query,
      model: model || 'qwen2.5-coder:7b'
    });

    res.status(200).json(response.data);
  } catch (error) {
    res.status(500).json({
      success: false,
      message: error.response?.data?.detail || error.message
    });
  }
};