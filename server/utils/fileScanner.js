import fs from 'fs';
import path from 'path';

const IGNORED_DIRS = new Set(['.git', 'node_modules', 'dist', 'build', 'venv', '__pycache__', '.vscode']);

export const getDirectoryTree = (dirPath) => {
  const stats = fs.statSync(dirPath);

  if (!stats.isDirectory()) {
    return {
      name: path.basename(dirPath),
      path: dirPath,
      type: 'file'
    };
  }

  const name = path.basename(dirPath);
  if (IGNORED_DIRS.has(name)) return null;

  const children = fs.readdirSync(dirPath)
    .map(child => getDirectoryTree(path.join(dirPath, child)))
    .filter(Boolean);

  return {
    name,
    path: dirPath,
    type: 'directory',
    children
  };
};