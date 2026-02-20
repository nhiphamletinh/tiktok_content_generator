#!/usr/bin/env python3
"""
Validate embeddings: pick one comment, compute cosine similarity to all others,
and print top-5 nearest neighbors with similarity scores.
"""
import argparse
import numpy as np
import pandas as pd
import random

random.seed(123)

EMB_FILE = "embeddings_local.npy"
CSV_FILE = "comments.csv"


def cosine_sim_matrix(vecs, v):
    # assume vecs: (n, d), v: (d,)
    # normalize
    vs = vecs / np.linalg.norm(vecs, axis=1, keepdims=True)
    v_norm = v / np.linalg.norm(v)
    sims = vs.dot(v_norm)
    return sims


def main():
    parser = argparse.ArgumentParser(description="Validate embeddings by printing top-K nearest neighbors for a comment")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--index", type=int, help="Row index to validate (0-based)")
    group.add_argument("--comment_id", type=int, help="comment_id value to validate")
    parser.add_argument("--top_k", type=int, default=5, help="Number of nearest neighbors to print")
    args = parser.parse_args()

    emb = np.load(EMB_FILE)
    df = pd.read_csv(CSV_FILE)
    n = len(df)
    if emb.shape[0] != n:
        print(f"Warning: embeddings ({emb.shape}) count != comments ({n})")

    # determine index
    if args.index is not None:
        idx = args.index
        if idx < 0 or idx >= n:
            raise SystemExit(f"Index out of range: {idx}")
    elif args.comment_id is not None:
        matches = df.index[df["comment_id"] == args.comment_id].tolist()
        if not matches:
            raise SystemExit(f"No comment with comment_id={args.comment_id}")
        idx = matches[0]
    else:
        # pick a random index deterministically
        idx = random.randrange(n)

    text = df.loc[idx, "text"]
    cid = df.loc[idx, "comment_id"]
    likes = df.loc[idx, "like_count"]

    print(f"Selected index {idx} (comment_id={cid}, like_count={likes}):")
    print(text)
    print(f"\nTop-{args.top_k} nearest neighbors:\n")

    sims = cosine_sim_matrix(emb, emb[idx])
    # exclude self by setting sim to -inf
    sims[idx] = -np.inf
    top_idxs = np.argsort(-sims)[: args.top_k]

    for rank, j in enumerate(top_idxs, start=1):
        sim = float(sims[j])
        jc = int(df.loc[j, "comment_id"])
        jlikes = int(df.loc[j, "like_count"])
        jtext = df.loc[j, "text"]
        print(f"{rank}. index={j} (comment_id={jc}, like_count={jlikes}) — sim={sim:.4f}")
        print(f"   {jtext}\n")


if __name__ == "__main__":
    main()
