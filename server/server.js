import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import codebaseRoutes from './routes/codebaseRoutes.js';

dotenv.config();

const app = express();
app.use(cors());
app.use(express.json());

app.use('/api/codebase', codebaseRoutes);

app.get('/health', (req, res) => {
  res.status(200).json({ status: 'ok', service: 'Express Gateway' });
});

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
  console.log(`Express Gateway server running on port ${PORT}`);
});