#!/usr/bin/env python3
"""
Hugging Face embedding pipeline (Inference API via requests)
- Loads `comments.csv`
- Extracts comment text
- Calls Hugging Face Inference API feature-extraction pipeline
  using a sentence-transformers model (default: all-MiniLM-L6-v2)
- Saves embeddings to `embeddings_hf.npy`
- Prints shape and verifies counts

Environment:
- HF_API_KEY must be set to a valid Hugging Face API token

Notes:
- Model options: `sentence-transformers/all-MiniLM-L6-v2` (fast, 384d),
  `sentence-transformers/all-mpnet-base-v2` (higher quality, 768d)
"""
import os
import sys
import time
from typing import List

import requests
import pandas as pd
import numpy as np

HF_API_KEY = os.getenv("HF_API_KEY")
if not HF_API_KEY:
    print("Error: HF_API_KEY environment variable not set.")
    sys.exit(1)

# Recommended default model for fast, high-quality semantic embeddings
# - `sentence-transformers/all-MiniLM-L6-v2`: small (384d), fast, cheap
# - `sentence-transformers/all-mpnet-base-v2`: larger (768d), higher quality
MODEL = os.getenv("HF_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
ENDPOINT = f"https://api-inference.huggingface.co/pipeline/feature-extraction/{MODEL}"
HEADERS = {"Authorization": f"Bearer {HF_API_KEY}"}

BATCH_SIZE = 25
MAX_RETRIES = 3
BACKOFF_FACTOR = 2.0


def get_embeddings_hf(texts: List[str]) -> List[List[float]]:
    """Call Hugging Face Inference API for a batch of texts.
    Returns list of embedding vectors.
    """
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            # The HF feature-extraction pipeline accepts a list of inputs for batch
            resp = requests.post(ENDPOINT, headers=HEADERS, json=texts, timeout=60)
            if resp.status_code == 200:
                data = resp.json()
                # data should be a list of embeddings (one per input)
                return data
            else:
                # Print helpful debug info and retry
                print(f"HF API returned {resp.status_code}: {resp.text}")
                wait = BACKOFF_FACTOR ** (attempt - 1)
                print(f"Retrying in {wait}s (attempt {attempt}/{MAX_RETRIES})...")
                time.sleep(wait)
        except Exception as e:
            wait = BACKOFF_FACTOR ** (attempt - 1)
            print(f"Request error (attempt {attempt}/{MAX_RETRIES}): {e}. Retrying in {wait}s...")
            time.sleep(wait)
    raise RuntimeError("Failed to get embeddings from Hugging Face after retries")


def main():
    df = pd.read_csv("comments.csv")
    texts = df["text"].astype(str).tolist()
    n = len(texts)
    print(f"Loaded {n} comments from comments.csv")

    all_embeddings = []
    for i in range(0, n, BATCH_SIZE):
        batch = texts[i : i + BATCH_SIZE]
        print(f"Processing batch {i // BATCH_SIZE + 1} (items {i} to {i+len(batch)-1}) using model {MODEL}...")
        try:
            embs = get_embeddings_hf(batch)
        except Exception as e:
            print(f"Fatal: failed to fetch embeddings for batch starting at {i}: {e}")
            sys.exit(1)

        # HF may return nested lists; ensure shape
        for item in embs:
            # If the pipeline returns tokens or other nested shapes, try to flatten
            if isinstance(item, list) and len(item) and isinstance(item[0], list):
                # Already a vector
                vec = item
            else:
                vec = item
            all_embeddings.append(vec)

        print(f"Batch done, total embeddings so far: {len(all_embeddings)}")

    arr = np.array(all_embeddings, dtype=np.float32)
    np.save("embeddings_hf.npy", arr)
    print(f"Saved embeddings to embeddings_hf.npy")
    print(f"Embeddings shape: {arr.shape}")

    if arr.shape[0] != n:
        print(f"Warning: number of embeddings ({arr.shape[0]}) != number of comments ({n})")
    else:
        print("Number of embeddings matches number of comments ✅")


if __name__ == "__main__":
    main()
