# FedLens Frontend

Static browser client for the FedLens FastAPI backend. It runs without a Node build step and can be hosted directly on Vercel.

## Local Run

Start the backend on `http://127.0.0.1:8000`, then serve this directory:

```bash
cd frontend
python3 -m http.server 4173
```

Open `http://127.0.0.1:4173`.

## Vercel Setup

Before deploying, set `window.FEDLENS_API_BASE_URL` in `config.js` to the public Render URL for the backend. Add the Vercel URL to the backend `CORS_ORIGINS` environment variable.
