# SHL Conversational Assessment Recommender

FastAPI service that recommends SHL **Individual Test Solutions** through stateless multi-turn dialogue.  
Live API: `https://shl-assignment-s3kp.onrender.com`

## Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Readiness check → `{"status":"ok"}` |
| POST | `/chat` | Next agent reply + optional recommendations |

`POST /chat` body:

```json
{
  "messages": [
    {"role": "user", "content": "Hiring a Java developer"},
    {"role": "assistant", "content": "What seniority level?"},
    {"role": "user", "content": "Mid-level, around 4 years"}
  ]
}
```

Response fields: `reply`, `recommendations` (0–10), `end_of_conversation`.

Note: the root URL `/` returns 404 by design. Evaluators should use `/health` and `/chat`.

## Local run

```powershell
cd shl-assessment-recommender
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
copy .env.example .env
```

Set in `.env`:

```env
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-sonnet-4-20250514
```

```powershell
python scripts\build_catalog.py
python scripts\build_index_cache.py
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Test:

```powershell
curl http://127.0.0.1:8000/health
python eval\replay.py --url http://127.0.0.1:8000
```

## Project layout

```
app/                 API, agent, catalog, retrieval
data/                catalog.json + baked index cache (Docker build)
eval/                Recall@10 replay scripts
docs/                approach.pdf (submission write-up)
scripts/             catalog/index build utilities
Dockerfile           Render deployment
```

## Deploy on Render

1. Connect GitHub repo to a Render Web Service (Docker).
2. Set env vars: `ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL=claude-sonnet-4-20250514`.
3. Health check path: `/health`.
4. After deploy, verify `/health` and a sample `/chat` call.

Docker pre-builds the catalog and FAISS index so the free tier can start without OOM.

## Submission (SHL form)

- **API URL:** `https://shl-assignment-s3kp.onrender.com`
- **Approach document:** `docs/approach.pdf` (2 pages, by Satvik Pandey)

The assignment asks for an approach document (max 2 pages); PDF is acceptable and included in the repo.

## Author

Satvik Pandey
