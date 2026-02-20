#!/usr/bin/env python3
"""
Embedding pipeline
- Loads `comments.csv`
- Extracts comment text
- Calls OpenAI embeddings (`text-embedding-3-small`) in batches
- Saves embeddings to `embeddings.npy`
- Prints shape and verifies counts

Reads `OPENAI_API_KEY` from environment
"""
import os
import time
import sys
from typing import List

import pandas as pd
import numpy as np

try:
    from openai import OpenAI
except Exception as e:
    print("Missing openai package. Install with: pip install openai")
    raise

API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    print("Error: OPENAI_API_KEY environment variable not set.")
    sys.exit(1)

# Initialize client with provided API key (openai>=1.0.0 interface)
client = OpenAI(api_key=API_KEY)
MODEL = "text-embedding-3-small"
BATCH_SIZE = 25  # between 20-50 as requested
MAX_RETRIES = 3
BACKOFF_FACTOR = 2.0


def get_embeddings(texts: List[str]) -> List[List[float]]:
    """Call OpenAI embeddings API for a list of texts; simple wrapper with retry."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = client.embeddings.create(model=MODEL, input=texts)
            # resp.data elements may be attr-accessible objects or dicts
            embs = [getattr(item, "embedding", item.get("embedding")) for item in resp.data]
            return embs
        except Exception as e:
            wait = BACKOFF_FACTOR ** (attempt - 1)
            print(f"Embedding API error (attempt {attempt}/{MAX_RETRIES}): {e}. Retrying in {wait}s...")
            time.sleep(wait)
    raise RuntimeError("Failed to get embeddings after retries")


def main():
    df = pd.read_csv("comments.csv")
    texts = df["text"].astype(str).tolist()
    n = len(texts)
    print(f"Loaded {n} comments from comments.csv")

    all_embeddings = []
    for i in range(0, n, BATCH_SIZE):
        batch = texts[i : i + BATCH_SIZE]
        print(f"Processing batch {i // BATCH_SIZE + 1} (items {i} to {i+len(batch)-1})...")
        try:
            embs = get_embeddings(batch)
        except Exception as e:
            print(f"Fatal: failed to fetch embeddings for batch starting at {i}: {e}")
            sys.exit(1)
        all_embeddings.extend(embs)
        print(f"Batch done, total embeddings so far: {len(all_embeddings)}")

    arr = np.array(all_embeddings, dtype=np.float32)
    np.save("embeddings.npy", arr)
    print(f"Saved embeddings to embeddings.npy")
    print(f"Embeddings shape: {arr.shape}")

    if arr.shape[0] != n:
        print(f"Warning: number of embeddings ({arr.shape[0]}) != number of comments ({n})")
    else:
        print("Number of embeddings matches number of comments ✅")


if __name__ == "__main__":
    main()
