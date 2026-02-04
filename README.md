# 🚀 AI Writing Assistant

A full-stack AI-powered writing assistant built with **FastAPI** and **React**.

## 📁 Project Structure

```
ai-writing-assistant/
├── backend/                 # FastAPI server
│   ├── main.py             # API code with streaming support
│   ├── requirements.txt    # Python dependencies
│   ├── Procfile           # Deployment configuration
│   └── .env.example       # Environment variables template
│
└── frontend/               # React app
    ├── src/
    │   ├── App.jsx        # Main React component
    │   ├── App.css        # Styles
    │   └── main.jsx       # Entry point
    ├── index.html
    ├── package.json
    └── vite.config.js
```

---

## 🛠️ Local Development Setup

### Prerequisites

- **Python 3.10+** - [Download](https://python.org)
- **Node.js 18+** - [Download](https://nodejs.org)
- **Anthropic API Key** - [Get one here](https://console.anthropic.com/)

### Step 1: Set Up the Backend

```bash
# Navigate to backend folder
cd backend

# Create a virtual environment (recommended)
python -m venv venv

# Activate it
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create your .env file
cp .env.example .env

# Edit .env and add your Anthropic API key
# ANTHROPIC_API_KEY=sk-ant-your-key-here

# Run the server
python main.py
```

✅ Backend should now be running at `http://localhost:8000`

📚 API docs available at `http://localhost:8000/docs`

### Step 2: Set Up the Frontend

```bash
# Open a new terminal and navigate to frontend folder
cd frontend

# Install dependencies
npm install

# Create your .env file
cp .env.example .env

# Run the development server
npm run dev
```

✅ Frontend should now be running at `http://localhost:5173`

---

## 🚢 Deployment

### Deploying the Backend to Railway

[Railway](https://railway.app) is a platform that makes deploying backends easy.

#### Step-by-Step:

1. **Create a Railway account** at [railway.app](https://railway.app)

2. **Create a new project**:
   - Click "New Project" → "Deploy from GitHub repo"
   - Connect your GitHub and select your repository
   - Choose the `backend` folder as the root directory

3. **Set environment variables**:
   - Go to your project → Variables tab
   - Add these variables:
     ```
     ANTHROPIC_API_KEY=sk-ant-your-key-here
     FRONTEND_URL=https://your-app.vercel.app
     ```

4. **Deploy**:
   - Railway auto-detects the Procfile and deploys
   - Once deployed, you'll get a URL like `https://your-app.up.railway.app`

5. **Copy your Railway URL** - you'll need it for the frontend!

### Alternative: Deploying Backend to Render

[Render](https://render.com) is another excellent option.

#### Step-by-Step:

1. **Create a Render account** at [render.com](https://render.com)

2. **Create a new Web Service**:
   - Click "New" → "Web Service"
   - Connect your GitHub repository
   - Set the **Root Directory** to `backend`

3. **Configure the service**:
   ```
   Name: ai-writing-assistant-api
   Environment: Python 3
   Build Command: pip install -r requirements.txt
   Start Command: uvicorn main:app --host 0.0.0.0 --port $PORT
   ```

4. **Add environment variables**:
   - Go to "Environment" tab
   - Add:
     ```
     ANTHROPIC_API_KEY=sk-ant-your-key-here
     FRONTEND_URL=https://your-app.vercel.app
     ```

5. **Deploy** and copy your Render URL!

---

### Deploying the Frontend to Vercel

[Vercel](https://vercel.com) is perfect for React apps.

#### Step-by-Step:

1. **Create a Vercel account** at [vercel.com](https://vercel.com)

2. **Import your project**:
   - Click "Add New" → "Project"
   - Import your GitHub repository
   - Set the **Root Directory** to `frontend`

3. **Configure build settings** (Vercel usually auto-detects these):
   ```
   Framework Preset: Vite
   Build Command: npm run build
   Output Directory: dist
   ```

4. **Add environment variable**:
   - Go to "Environment Variables"
   - Add:
     ```
     VITE_API_URL=https://your-backend-url.railway.app
     ```
   (Use your Railway or Render URL from the previous step)

5. **Deploy**!

6. **Update your backend** with the Vercel URL:
   - Go back to Railway/Render
   - Update `FRONTEND_URL` to your Vercel URL

---

## 🔗 Connecting Everything

After deployment, you need to connect the frontend and backend:

| Service | Environment Variable | Value |
|---------|---------------------|-------|
| Backend (Railway/Render) | `FRONTEND_URL` | Your Vercel URL (e.g., `https://my-app.vercel.app`) |
| Frontend (Vercel) | `VITE_API_URL` | Your Railway/Render URL (e.g., `https://my-app.up.railway.app`) |

---

## 📖 API Reference

### `POST /generate`

Generate content (non-streaming).

**Request:**
```json
{
  "prompt": "Write a blog post about Python",
  "writing_type": "blog_post",
  "tone": "professional"
}
```

**Response:**
```json
{
  "content": "Generated text...",
  "model": "claude-sonnet-4-20250514",
  "usage": {
    "input_tokens": 50,
    "output_tokens": 500
  }
}
```

### `POST /generate/stream`

Generate content with streaming (Server-Sent Events).

**Request:** Same as above

**Response:** Text stream in SSE format:
```
data: Here is
data: your content
data: streaming...
data: [DONE]
```

---

## 🧪 Testing Your API

You can test your API using curl:

```bash
# Test the root endpoint
curl http://localhost:8000/

# Test content generation
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Write a haiku about coding", "tone": "casual"}'

# Test streaming (you'll see text appear gradually)
curl -X POST http://localhost:8000/generate/stream \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Write a short story", "tone": "casual"}'
```

---

## 🔒 Security Notes

1. **Never commit `.env` files** - they contain secrets!
2. **Use CORS properly** - only allow your frontend's domain
3. **Consider rate limiting** in production
4. **Use HTTPS** - both Railway and Vercel provide this automatically

---

## 📚 Learning Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [Anthropic API Docs](https://docs.anthropic.com/)
- [Vite Guide](https://vitejs.dev/guide/)

---

## 🤝 Need Help?

- Check the API docs at `/docs` endpoint
- Open an issue on GitHub
- Read the inline code comments - they explain everything!

Happy coding! 🎉
