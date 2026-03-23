# Creator Insight — AI prototype for TikTok creators

A compact, end-to-end prototype that turns TikTok comment threads into script-ready, retention-optimized content outlines. Built as a local-first demo showcasing practical LLM workflows, prompt engineering, and a fast product loop.

This repo contains a working prototype with:
- a local embedding pipeline (sentence-transformers)
- semantic clustering (KMeans) and demand scoring
- an LLM-driven generator that outputs strict JSON outlines optimized for retention
- a minimal Flask frontend to run analysis and preview script-ready recommendations

What this tool does:
- Builds AI workflows and agents: full pipeline from raw comments → embeddings → clusters → LLM insights. The project demonstrates how to compose ML components into a productized flow.
- Automates content creation: produces TikTok-first hooks, retention strategies, and CTAs ready for creators to record and post.
- Rapid prototyping & experimentation: local models, caching, debug logs, and a clear A/B testing plan for watch-time and comments-per-view.
- Cross-functional scope: you can extend this prototype with design, analytics, and backend engineering for real-world integration.

Highlights for reviewers
- Strict, JSON-only prompt schema enforced by `comment_insights.py` so outputs are production-friendly and parseable:

```json
{
  "cluster_title": "...",
  "creator_angle": "...",
  "content_format": "...",
  "hook": "...",
  "retention_strategy": "...",
  "body_outline": ["...","...","..."],
  "engagement_cta": "..."
}
```

- Files to inspect:
  - `comments.csv` — canonical comment input
  - `embedding_pipeline_local.py` → `embeddings_local.npy`
  - `cluster_insights.py` → generates `clusters.json`
  - `compute_cluster_scores.py` → `cluster_scores.json`
  - `comment_insights.py` → generates `cluster_insights.json` (LLM-driven)
  - `frontend/app.py`, `frontend/templates/index.html`, `frontend/static/app.js` — demo UI

LLM & prompt engineering
- Current prototype uses a local Ollama model (`llama3.1`) to avoid remote costs and enable reproducible demos. The `comment_insights.py` script:
  - builds a strict prompt that enforces the creator-first JSON schema
  - includes retries, balanced-brace JSON extraction, and debug dumps (`debug_output_cluster_{cid}.txt`)
  - caches outputs in `cluster_insights.json` to avoid repeated calls

- Claude compatibility: reviewers who prefer Claude can adapt the LLM step easily. Replace the Ollama call in `comment_insights.py` with an Anthropic/Claude client call (pseudocode):

```python
from anthropic import Anthropic
client = Anthropic(api_key=os.environ['CLAUDE_API_KEY'])
resp = client.create_completion(model='claude-2.1', prompt=prompt, max_tokens=600, temperature=0.2)
model_text = resp['completion']
```

Design & product decisions (concise)
- Retention-first output: hooks with pattern-interrupts and creator framing ("Nobody talks about this..."), explicit retention mechanics (open loop / escalation / step reveal), and CTAs that trigger identity-based comments.
- Prioritization: demand score uses z-score normalization, weighting likes=0.6 and cluster size=0.4 to surface high-impact clusters first.
- Safety & reliability: strict JSON prompt, parse-validation, retry lower-temp fallback, and raw debug files for annotation.

How to run (local dev)

1. Create and activate a Python venv and install dependencies (project expects a `.venv`):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Produce embeddings and cluster (or just run the Flask UI which triggers them):

```bash
# Run the dev server (the /analyze endpoint runs embedding + clustering)
.venv/bin/python frontend/app.py
# Open http://127.0.0.1:8501 in your browser
```

3. Generate LLM insights (the endpoint `/recommend` runs `comment_insights.py`). You can also run it directly:

```bash
.venv/bin/python comment_insights.py
# Results written to cluster_insights.json; raw model outputs saved as debug_output_cluster_<id>.txt
```
# Creator Insight

Creator Insight is an end-to-end prototype that converts TikTok comment threads into short, script-ready content outlines optimized for retention and engagement. The project illustrates an LLM-driven product workflow: data ingestion → embeddings → clustering → LLM-generated recommendations → lightweight frontend for experimentation.

This README follows a conventional technical structure so you can run the project locally and understand the product and technical choices.

## Features

- Local embedding pipeline using `sentence-transformers`
- Semantic clustering (KMeans) to surface comment themes
- Demand scoring to prioritize high-impact clusters (z-score blend of likes and cluster size)
- LLM-driven generator that produces strict, JSON-formatted, creator-first outlines (hook, retention tactic, bulletized body, CTA)
- Minimal Flask + SPA frontend to trigger analysis and preview recommendations
- Caching, parse-validation, and debug outputs to improve reliability

## Repository structure

- `comments.csv` — canonical input comments dataset
- `embedding_pipeline_local.py` — creates `embeddings_local.npy`
- `cluster_insights.py` — clustering helper (produces `clusters.json`)
- `compute_cluster_scores.py` — demand scoring (produces `cluster_scores.json`)
- `comment_insights.py` — LLM prompt + generator (produces `cluster_insights.json` and debug outputs)
- `frontend/` — Flask app, templates and JS for demo UI
- `docs/architecture.svg` — architecture diagram

## Quickstart (local)

1. Create a virtual environment and install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Run the dev server (this triggers the pipelines via endpoints):

```bash
.venv/bin/python frontend/app.py
# open http://127.0.0.1:8501
```

3. Or run the pipeline scripts manually:

```bash
.venv/bin/python embedding_pipeline_local.py    # creates embeddings_local.npy
.venv/bin/python cluster_insights.py          # creates clusters.json
.venv/bin/python comment_insights.py          # generates cluster_insights.json (LLM step)
```

Generated artifacts:

- `embeddings_local.npy` — embedding matrix for comments
- `clusters.json` — cluster metadata and representative comments
- `cluster_scores.json` — demand scores per cluster
- `cluster_insights.json` — final LLM-generated outlines (cached)

## LLM & Prompt Engineering

`comment_insights.py` contains the core prompt and parsing logic. Key practices applied:

- Strict JSON-only prompt template to reduce hallucinations and produce machine-parseable outputs
- Example output included in the prompt to guide format and tone (creator-first)
- Balanced-brace JSON extractor with retries and debug file dumps (`debug_output_cluster_{cid}.txt`)
- Local-first approach using Ollama (`llama3.1`) for reproducible demos; easily replaceable with Claude/other LLMs

Example output schema:

```json
{
  "cluster_title": "...",
  "creator_angle": "...",
  "content_format": "...",
  "hook": "...",
  "retention_strategy": "...",
  "body_outline": ["...","...","..."],
  "engagement_cta": "..."
}
```

### Claude compatibility

To adapt the LLM step to Claude, replace the Ollama invocation in `comment_insights.py` with a Claude/Anthropic client call. Ensure you keep the prompt structure, temperature control, and the JSON parse/validation flow.

## Design decisions & challenges

- Retention-first outputs: prompt engineering focuses on hooks, open loops, and CTAs that drive comments and watch-time rather than neutral summaries.
- Reliability: strict schema + parsing + retries mitigate LLM noise and allow caching of stable outputs.
- Prioritization: demand scoring balances engagement signals (likes) and cluster prevalence so recommendations surface high-impact ideas first.

## Suggested experiments & metrics

- A/B test creators using generated scripts vs. control. Measure: watch time, completion rate, comments-per-view, and time-to-publish.
- Track which cluster templates are used and correlate outline elements (hook/CTA) with engagement lift.


If you want, I can now:
- produce a short 9‑slide deck that follows the 5‑minute script, or
- add a Claude integration stub in `comment_insights.py` and a demo run (requires API key).
