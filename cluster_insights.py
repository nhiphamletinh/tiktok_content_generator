#!/usr/bin/env python3
"""
Cluster embeddings and extract structured insights.

- Loads `embeddings_local.npy` and `comments.csv`
- Asserts row counts match
- L2-normalizes embeddings
- Runs KMeans with n_clusters=5 (random_state=42, n_init=10)
- For each cluster, finds top-5 comments closest to centroid
- Appends `cluster_id` to dataframe and saves `clusters.json`
- Prints cluster summaries to stdout
"""
import os
import json
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import normalize

EMB_FILE = "embeddings_local.npy"
CSV_FILE = "comments.csv"
OUT_JSON = "clusters.json"
N_CLUSTERS = 5
TOP_K = 5


def cosine_sim(a, b):
    # a, b expected normalized -> cosine similarity is dot product
    return np.dot(a, b)


def main():
    if not os.path.exists(EMB_FILE) or not os.path.exists(CSV_FILE):
        raise SystemExit("Missing embeddings_local.npy or comments.csv. Run previous steps first.")

    emb = np.load(EMB_FILE)
    df = pd.read_csv(CSV_FILE)

    # 1) Verify shape alignment
    n_comments = len(df)
    if emb.shape[0] != n_comments:
        raise SystemExit(f"Shape mismatch: embeddings rows={emb.shape[0]} != comments rows={n_comments}")
    print(f"Loaded {n_comments} comments and embeddings (dim={emb.shape[1]})")

    # 2) Normalize embeddings (L2)
    emb_norm = normalize(emb, norm="l2", axis=1)
    print("Normalized embeddings (L2).")

    # 3) Run KMeans
    print(f"Running KMeans (n_clusters={N_CLUSTERS})...")
    kmeans = KMeans(n_clusters=N_CLUSTERS, random_state=42, n_init=10)
    labels = kmeans.fit_predict(emb_norm)
    print("KMeans finished.")

    df["cluster_id"] = labels

    # compute centroids in normalized space
    centroids = kmeans.cluster_centers_
    # Ensure centroids are normalized (they should be, but renormalize for safety)
    centroids = normalize(centroids, norm="l2", axis=1)
    # attempt to read existing LLM-generated cluster titles (from comment_insights.py)
    llm_titles = {}
    if os.path.exists("cluster_insights.json"):
        try:
            with open("cluster_insights.json", "r", encoding="utf-8") as f:
                llm_entries = json.load(f)
                # llm_entries expected to be a list of dicts with cluster_id and cluster_title
                for e in llm_entries:
                    try:
                        llm_titles[int(e.get("cluster_id"))] = str(e.get("cluster_title", "")).strip()
                    except Exception:
                        continue
        except Exception:
            llm_titles = {}

    clusters_out = {}

    for cid in range(N_CLUSTERS):
        idxs = np.where(labels == cid)[0]
        size = len(idxs)
        # compute similarities of each member to centroid
        sims = []
        for i in idxs:
            sim = float(cosine_sim(emb_norm[i], centroids[cid]))
            sims.append((i, sim))
        # sort descending by sim
        sims_sorted = sorted(sims, key=lambda x: -x[1])
        top = sims_sorted[:TOP_K]
        rep_comments = []
        for i, sim in top:
            row = df.iloc[i]
            rep_comments.append({
                "index": int(i),
                "comment_id": int(row["comment_id"]),
                "like_count": int(row["like_count"]),
                "text": str(row["text"]),
                "similarity": float(sim),
            })
        # Name: prefer LLM-derived short title if available, otherwise derive a short name
        name = llm_titles.get(cid)
        if not name:
            # fallback: create a short name from the top representative comment
            if rep_comments:
                sample = rep_comments[0]["text"]
                # take first 4 words as a compact name
                words = sample.split()
                name = " ".join(words[:4])
            else:
                name = f"Cluster {cid}"

        clusters_out[str(cid)] = {
            "size": size,
            "name": name,
            "representative_comments": rep_comments,
        }

        # Print summary
        print(f"\nCluster {cid}: size={size}")
        print("Representative comments:")
        for rc in rep_comments:
            print(f" - (sim={rc['similarity']:.4f}) [{rc['comment_id']}] {rc['text']}")

    # 5) Save structured output
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(clusters_out, f, ensure_ascii=False, indent=2)

    print(f"\nSaved cluster summaries to {OUT_JSON}")


if __name__ == "__main__":
    main()
