# Portfolio RAG chatbot

Browser -> Next.js `/api/chat` (proxy: secret + visitor IP) -> FastAPI `/chat` (retrieve from Qdrant -> OpenAI answer, streamed)

- `backend/`  -> its own repo/folder, deploy on Render
- `frontend/` -> 2 files + env, copy into the portfolio repo (same paths)

## Backend
    conda create -n portfolio_rag python=3.11 -y
    conda activate portfolio_rag
    pip install -r requirements.txt
    copy .env.example .env        (fill values)
    python -m app.ingest          (after every edit in knowledge/)
    uvicorn app.main:app --reload --port 8000
    open http://localhost:8000/docs

## Frontend (portfolio repo)
1. copy `src/components/chatbot/ChatWidget.tsx` and `src/app/api/chat/route.ts`
2. `.env.local` from `.env.local.example`
3. in `src/app/layout.tsx`: `import ChatWidget from "@/components/chatbot/ChatWidget";` and add `<ChatWidget />` after `{children}` inside `<body>`

## Deploy
- Render web service: root dir `backend`, build `pip install -r requirements.txt`, start `uvicorn app.main:app --host 0.0.0.0 --port $PORT`, env vars from `.env.example`
- Vercel: env `RAG_API_URL` (Render URL, no trailing slash) + `RAG_API_SECRET`, then redeploy
