AI Creator Insight Tool — Layer 1 & 2

Contents:
- `generate_comments.py`: Generates 200 synthetic TikTok-style comments and writes `comments.csv`.
- `comments.csv`: Generated dataset (200 comments).
- `embedding_pipeline.py`: Loads `comments.csv`, requests OpenAI embeddings (`text-embedding-3-small`) in batches and saves `embeddings.npy`.
- `requirements.txt`: Python dependencies (`pandas`, `numpy`, `openai`).

Quick usage:

1) Generate comments (script already included):

```bash
python3 generate_comments.py
```

2) Install deps and run embeddings (requires `OPENAI_API_KEY`):

```bash
pip install -r requirements.txt
export OPENAI_API_KEY="your_key_here"
python3 embedding_pipeline.py
```

Notes:
- `embedding_pipeline.py` uses batching and simple retry/backoff.
- The scripts are intentionally minimal and produce console progress logs.
