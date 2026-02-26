AI Creator Insight Tool — Layer 1 & 2

Contents:
- `comments.csv`: Dataset of 200 synthetic TikTok-style comments (already present).
- `embedding_pipeline.py`: Loads `comments.csv`, requests OpenAI embeddings (`text-embedding-3-small`) in batches and saves `embeddings.npy`.
- `embedding_pipeline_local.py`: Local embedding pipeline using `sentence-transformers` and saves `embeddings_local.npy`.
- `cluster_insights.py`: Clusters embeddings and writes `clusters.json` with representative comments.
- `validate_embeddings.py`: Utility to print nearest neighbors for validation.
- `requirements.txt`: Python dependencies (`pandas`, `numpy`, `openai`, `requests`).

Quick usage (use existing `comments.csv` in the repo):

1) Create and activate a virtualenv:

```bash
cd "/home/user/tiktok oa app"
python3 -m venv .venv
source .venv/bin/activate
```

2) Install dependencies:

```bash
pip install --upgrade pip
pip install -r requirements.txt
pip install sentence-transformers scikit-learn
```

3) Produce embeddings locally (recommended):

```bash
python3 embedding_pipeline_local.py
```

4) Run clustering and extract insights:

```bash
python3 cluster_insights.py
```

5) Validate nearest neighbors for sanity checks:

```bash
python3 validate_embeddings.py --index 10 --top_k 5
```

Notes:
- This repo now uses the existing `comments.csv` as the authoritative dataset; the generator file has been removed.
- Use `LOCAL_EMBEDDING_MODEL` env var to change the local embedding model (e.g., `all-mpnet-base-v2`).
- Model downloads may take time the first run.
