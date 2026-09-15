import express from 'express';
import { 
  getFileTree, 
  getFileContent, 
  indexRepository, 
  queryCodebase,
  refactorCode 
} from '../controllers/codebaseController.js';

const router = express.Router();

router.get('/tree', getFileTree);
router.get('/file-content', getFileContent);
router.post('/index', indexRepository);
router.post('/query', queryCodebase);
router.post('/refactor', refactorCode);

export default router;