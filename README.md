# SHL Conversational Assessment Recommender

Stateless FastAPI service that recommends SHL **Individual Test Solutions** through multi-turn dialogue, grounded in the official catalog.

## API (assignment schema)

| Endpoint | Response |
|----------|----------|
| `GET /health` | `{"status": "ok"}` |
| `POST /chat` | `reply`, `recommendations` (0–10), `end_of_conversation` |

## Local setup

```powershell
cd shl-assessment-recommender
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

Edit `.env`:

```env
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-sonnet-4-20250514
```

```powershell
python scripts\build_catalog.py
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

First start loads the embedding index (~30–60s). Then test:

```powershell
curl http://127.0.0.1:8000/health
```

## Evaluation

```powershell
python eval\replay.py --url http://127.0.0.1:8000
python eval\run_eval.py
```

## Deploy on Render

1. Push this project folder to GitHub.
2. In Render, create a **Web Service** and connect the repo.
3. Use **Docker** runtime (the included `Dockerfile` is used automatically).
4. Add environment variables:
   - `ANTHROPIC_API_KEY` = your Anthropic key
   - `ANTHROPIC_MODEL` = `claude-sonnet-4-20250514`
5. Ensure health check path is `/health`.
6. Deploy and wait for the build to complete.
7. Verify:
   - `GET /health` returns `{"status":"ok"}`
   - `POST /chat` returns valid assignment schema

Notes:
- First cold start can be slower because embeddings/index initialize.
- Keep the service warm before submission if using free tier.

## Submission checklist

- [ ] GitHub repo contains `shl-assessment-recommender/` (not PDFs or `.env`)
- [ ] Render service live; `/health` and `/chat` public
- [ ] `ANTHROPIC_API_KEY` set on Render
- [ ] Submit API URL + `docs/approach.md` via SHL form

## Layout

```
app/          API, agent, catalog, retrieval
data/         catalog.json (370 items)
eval/         Recall@10, replay
docs/         approach.md (≤2 pages)
Dockerfile    production image
```

Sample conversations for eval live in `../sample_conversations/` (reference only).
