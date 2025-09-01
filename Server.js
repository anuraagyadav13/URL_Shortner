import express from 'express';
import mongoose from 'mongoose';
import path from 'path';
import { fileURLToPath } from 'url';
import { shortUrl, getOriginalUrl } from './Controller/url.js';

const app = express();
const port = 4000;

// Setup __dirname in ES module scope
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Middleware
app.use(express.urlencoded({ extended: true }));
app.use(express.static('public'));

// View engine setup
app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));

// MongoDB connection
mongoose
  .connect('mongodb+srv://anutechx2707:CSbNs9v9QjJYtL2U@cluster0.ockiyc0.mongodb.net/', {
    dbName: 'URL_Shortner',
  })
  .then(() => console.log('MongoDB Connected..!'))
  .catch((err) => console.error('MongoDB Connection Error:', err));

// Routes
app.get('/', (req, res) => {
  res.render('index', { shortUrl: null });
});

app.post('/short', shortUrl);
app.get('/:shortCode', getOriginalUrl);

// Start server
app.listen(port, () => {
  console.log(`Server running at: http://localhost:${port}`);
});

