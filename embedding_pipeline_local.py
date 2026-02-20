#!/usr/bin/env python3
"""
Local embedding pipeline using sentence-transformers
- Loads `comments.csv`
- Encodes texts with SentenceTransformer
- Saves embeddings to `embeddings_local.npy`
- Prints shape and verifies counts

No external API key required. Uses the local model cache.
"""
import os
import sys
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer

MODEL = os.getenv("LOCAL_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
BATCH_SIZE = int(os.getenv("LOCAL_BATCH_SIZE", "64"))


def main():
    if not os.path.exists("comments.csv"):
        print("Error: comments.csv not found. Run generate_comments.py first.")
        sys.exit(1)

    df = pd.read_csv("comments.csv")
    texts = df["text"].astype(str).tolist()
    n = len(texts)
    print(f"Loaded {n} comments from comments.csv")

    print(f"Loading model {MODEL} (this may download weights the first time)...")
    model = SentenceTransformer(MODEL)
    print("Model loaded.")

    all_embeddings = []
    for i in range(0, n, BATCH_SIZE):
        batch = texts[i : i + BATCH_SIZE]
        print(f"Encoding batch {i // BATCH_SIZE + 1} (items {i} to {i+len(batch)-1})...")
        embs = model.encode(batch, batch_size=BATCH_SIZE, show_progress_bar=False)
        # embs is numpy array or list of vectors
        for v in embs:
            all_embeddings.append(v)

    arr = np.array(all_embeddings, dtype=np.float32)
    np.save("embeddings_local.npy", arr)
    print(f"Saved embeddings to embeddings_local.npy")
    print(f"Embeddings shape: {arr.shape}")

    if arr.shape[0] != n:
        print(f"Warning: number of embeddings ({arr.shape[0]}) != number of comments ({n})")
    else:
        print("Number of embeddings matches number of comments ✅")


if __name__ == "__main__":
    main()
