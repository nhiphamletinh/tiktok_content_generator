#!/usr/bin/env python3
"""Compute engagement-weighted demand scores per cluster.

- Loads `embeddings_local.npy` and `comments.csv`.
- Runs KMeans with the same parameters as `cluster_insights.py` to get cluster assignments.
- For each cluster computes:
  - `size`: number of comments
  - `sum_likes`: total likes in cluster
  - `avg_likes`: average likes per comment
  - `demand_score`: engagement-weighted score = `sum_likes * sqrt(size)` (gives modest boost to larger clusters)
- Outputs `cluster_scores.json` sorted by `demand_score` descending.

You can tweak the `demand_score` formula as desired.
"""
import os
import json
import math
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import normalize

EMB_FILE = "embeddings_local.npy"
CSV_FILE = "comments.csv"
OUT_FILE = "cluster_scores.json"
N_CLUSTERS = 5


def _z_scores(arr: np.ndarray) -> np.ndarray:
    """Compute z-scores for a 1-D numpy array. Returns zeros if std is zero."""
    mean = float(np.mean(arr))
    std = float(np.std(arr, ddof=0))
    if std == 0:
        return np.zeros_like(arr, dtype=float)
    return (arr - mean) / std


def main():
    if not os.path.exists(EMB_FILE) or not os.path.exists(CSV_FILE):
        raise SystemExit("Missing embeddings_local.npy or comments.csv. Run the embedding pipeline first.")

    emb = np.load(EMB_FILE)
    df = pd.read_csv(CSV_FILE)

    if emb.shape[0] != len(df):
        raise SystemExit(f"Mismatch: embeddings rows={emb.shape[0]} vs comments rows={len(df)}")

    emb_norm = normalize(emb, norm="l2", axis=1)

    # Run KMeans with same settings used before
    kmeans = KMeans(n_clusters=N_CLUSTERS, random_state=42, n_init=10)
    labels = kmeans.fit_predict(emb_norm)

    df["cluster_id"] = labels

    # gather per-cluster stats
    cluster_stats = []
    for cid in range(N_CLUSTERS):
        subset = df[df["cluster_id"] == cid]
        size = int(len(subset))
        sum_likes = int(subset["like_count"].sum()) if size > 0 else 0
        avg_likes = float(sum_likes) / size if size > 0 else 0.0
        cluster_stats.append({
            "cluster_id": int(cid),
            "size": size,
            "sum_likes": sum_likes,
            "avg_likes": round(avg_likes, 4),
        })

    # Convert to arrays for normalization
    sizes = np.array([c["size"] for c in cluster_stats], dtype=float)
    sums = np.array([c["sum_likes"] for c in cluster_stats], dtype=float)

    # compute z-scores
    z_sizes = _z_scores(sizes)
    z_sums = _z_scores(sums)

    # weights (likes=0.6, size=0.4)
    w_likes = 0.6
    w_size = 0.4

    for i, c in enumerate(cluster_stats):
        z_like = float(z_sums[i])
        z_size = float(z_sizes[i])
        demand_score = float(w_likes * z_like + w_size * z_size)
        c.update({
            "z_sum_likes": round(z_like, 4),
            "z_size": round(z_size, 4),
            "demand_score": round(demand_score, 4),
        })

    results_sorted = sorted(cluster_stats, key=lambda x: -x["demand_score"])

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results_sorted, f, ensure_ascii=False, indent=2)

    print(f"Saved cluster scores to {OUT_FILE}")


if __name__ == "__main__":
    main()
