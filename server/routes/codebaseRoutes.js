import express from 'express';
import { 
  getFileTree, 
  getFileContent, 
  indexRepository, 
  queryCodebase, 
  getDependencyGraph, 
  refactorCode, 
  reviewGitDiff
} from '../controllers/codebaseController.js';

const router = express.Router();

router.get('/tree', getFileTree);
router.get('/file-content', getFileContent);
router.post('/index', indexRepository);
router.post('/query', queryCodebase);
router.get("/graph/:projectId", getDependencyGraph);
router.post("/refactor-code", refactorCode);
router.post("/git-diff-review", reviewGitDiff);

export default router;