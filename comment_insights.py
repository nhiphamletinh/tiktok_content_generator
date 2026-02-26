#!/usr/bin/env python3
"""Generate structured TikTok content insights per cluster using a local Llama 3 8B Instruct model.

Requirements:
- Uses `comments.csv`, `clusters.json`, and `cluster_scores.json` to build prompts.
- Re-runs KMeans clustering (same params) to get cluster assignments for selecting top comments.
- Calls local Ollama model (if available) to generate strict JSON per cluster.
- Uses `transformers` tokenizer when available to estimate/truncate prompt length.
- Caches outputs in `cluster_insights.json` and only regenerates when `demand_score` changes significantly.

Usage: run inside the project's venv where `ollama` (CLI or python package) may be installed.
"""
import os
import json
import time
import math
import subprocess
from typing import Optional

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import normalize

try:
    # transformers tokenizer for truncation/length estimation
    from transformers import AutoTokenizer
    HAVE_TOKENIZER = True
except Exception:
    HAVE_TOKENIZER = False


CSV_FILE = "comments.csv"
EMB_FILE = "embeddings_local.npy"
CLUSTERS_JSON = "clusters.json"
SCORES_JSON = "cluster_scores.json"
OUT_JSON = "cluster_insights.json"
N_CLUSTERS = 5

# Model settings
MODEL_NAME = os.environ.get("OLLAMA_MODEL", "llama3.1")
TEMPERATURE = 0.3
MAX_NEW_TOKENS = 400
TOP_P = 0.9

# Cache threshold for demand_score change
DEMAND_SCORE_EPS = 1e-3


EXAMPLE_OUTPUT = {
    "cluster_title": "Visa timing",
    "pain_point": "Applicants are unsure about visa processing timelines and how it affects intake planning.",
    "video_outline": {
        "hook": "Visa taking forever? Plan this instead.",
        "body": "Briefly explain typical visa timelines, common delays, and one practical step applicants can take to avoid last-minute problems.",
        "cta": "Comment your timeline—I’ll reply with tips."
    }
}


def find_balanced_json(s: str) -> Optional[str]:
    """Find the first balanced JSON object in string s. Returns substring or None."""
    start = s.find("{")
    if start == -1:
        return None
    depth = 0
    for i in range(start, len(s)):
        ch = s[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return s[start : i + 1]
    return None


def call_ollama_cli(prompt: str, temperature: float, max_tokens: int, top_p: float) -> str:
    """Call local ollama CLI as a fallback. Returns model output string."""
    # Ollama CLI doesn't accept temperature/max-tokens/top-p flags universally.
    # Keep the CLI invocation minimal and pass the prompt via stdin; prefer python client when available.
    cmd = [
        "ollama",
        "run",
        MODEL_NAME,
    ]
    try:
        proc = subprocess.run(cmd, input=prompt.encode("utf-8"), stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        out = proc.stdout.decode("utf-8", errors="ignore")
        err = proc.stderr.decode("utf-8", errors="ignore")
        if err:
            return out + "\n\n=== STDERR ===\n" + err
        return out
    except FileNotFoundError:
        raise RuntimeError("ollama CLI not found; please install ollama or provide a transformer-based fallback.")


def safe_token_count(prompt: str, tokenizer_name: str = "gpt2") -> int:
    if HAVE_TOKENIZER:
        try:
            tok = AutoTokenizer.from_pretrained(tokenizer_name)
            tokens = tok(prompt, return_tensors=None, truncation=False)
            return len(tokens["input_ids"]) if "input_ids" in tokens else 0
        except Exception:
            pass
    # fallback: naive whitespace token count
    return len(prompt.split())


def build_prompt(comments: list) -> str:
    """Build the strict prompt with an example output and the comments list."""
    system_inst = (
        'SYSTEM INSTRUCTION:\n"You are a TikTok content strategist.\nYour job is to analyze audience questions and extract one clear content opportunity.\nYou MUST return valid JSON only. No explanations. No extra text."\n\n'
    )

    user_preamble = "USER PROMPT STRUCTURE:\nAnalyze the following audience comments:\n\n"

    example = json.dumps(EXAMPLE_OUTPUT, ensure_ascii=False)
    example_block = f"EXAMPLE_OUTPUT:\n{example}\n\n"

    comments_block = ""
    for c in comments:
        # sanitize newlines
        text = c.replace('\n', ' ').strip()
        comments_block += text + "\n"

    template = (
        system_inst + user_preamble + example_block + "COMMENTS:\n" + comments_block + "\n"
        + "Produce JSON in EXACTLY this format:\n{\n"
        + '"cluster_title": "max 4 words",\n'
        + '"pain_point": "one sentence describing the core audience frustration",\n'
        + '"video_outline": {\n"hook": "strong curiosity-driven first sentence under 15 words",\n'
        + '"body": "2-3 sentences explaining the core idea clearly",\n'
        + '"cta": "short engagement call-to-action"\n}\n}\n'
        + "Rules:\nHook must create a curiosity gap.\nBody must directly answer the dominant tension in comments.\nCTA must invite interaction (comment, save, follow).\nNo emojis. No markdown. Output must be valid JSON only."
    )

    # ensure prompt isn't absurdly long; truncate comments if necessary
    max_ctx = 2048
    token_count = safe_token_count(template)
    if token_count > max_ctx:
        # truncate each comment to 200 chars and rebuild
        truncated = [c[:200] for c in comments]
        comments_block = "".join([t.replace('\n', ' ').strip() + "\n" for t in truncated])
        template = system_inst + user_preamble + example_block + "COMMENTS:\n" + comments_block + "\n" + (
            "Produce JSON in EXACTLY this format:\n{\n"
            + '"cluster_title": "max 4 words",\n'
            + '"pain_point": "one sentence describing the core audience frustration",\n'
            + '"video_outline": {\n"hook": "strong curiosity-driven first sentence under 15 words",\n'
            + '"body": "2-3 sentences explaining the core idea clearly",\n'
            + '"cta": "short engagement call-to-action"\n}\n}\n'
            + "Rules:\nHook must create a curiosity gap.\nBody must directly answer the dominant tension in comments.\nCTA must invite interaction (comment, save, follow).\nNo emojis. No markdown. Output must be valid JSON only."
        )

    return template


def parse_model_output(text: str) -> Optional[dict]:
    blk = find_balanced_json(text)
    if not blk:
        return None
    try:
        data = json.loads(blk)
        return data
    except Exception:
        return None


def main():
    if not os.path.exists(CSV_FILE) or not os.path.exists(EMB_FILE) or not os.path.exists(SCORES_JSON):
        raise SystemExit("Missing required files: comments.csv, embeddings_local.npy, or cluster_scores.json")

    df = pd.read_csv(CSV_FILE)
    emb = np.load(EMB_FILE)

    if emb.shape[0] != len(df):
        raise SystemExit("Embeddings / comments count mismatch")

    # Re-run clustering to assign cluster ids
    emb_norm = normalize(emb, norm="l2", axis=1)
    kmeans = KMeans(n_clusters=N_CLUSTERS, random_state=42, n_init=10)
    labels = kmeans.fit_predict(emb_norm)
    df["cluster_id"] = labels

    # load clusters.json to get centroid-representative mapping if present
    clusters_map = {}
    if os.path.exists(CLUSTERS_JSON):
        with open(CLUSTERS_JSON, "r", encoding="utf-8") as f:
            clusters_map = json.load(f)

    # load cluster scores
    with open(SCORES_JSON, "r", encoding="utf-8") as f:
        scores = json.load(f)
    score_map = {int(item["cluster_id"]): float(item.get("demand_score", 0.0)) for item in scores}

    # load existing cache
    cache = {}
    if os.path.exists(OUT_JSON):
        try:
            with open(OUT_JSON, "r", encoding="utf-8") as f:
                entries = json.load(f)
                cache = {int(e["cluster_id"]): e for e in entries}
        except Exception:
            cache = {}

    results = []

    # process clusters in descending demand order
    cluster_order = sorted(score_map.items(), key=lambda x: -x[1])

    for cid, demand in cluster_order:
        cid = int(cid)
        existing = cache.get(cid)
        if existing and abs(float(existing.get("demand_score", 0.0)) - float(demand)) < DEMAND_SCORE_EPS:
            print(f"Cluster {cid}: cached and unchanged; skipping model call")
            results.append(existing)
            continue

        subset = df[df["cluster_id"] == cid].copy()
        if subset.empty:
            print(f"Cluster {cid}: no comments found; skipping")
            continue

        # select top 5 comments by like_count
        top5 = subset.sort_values("like_count", ascending=False).head(5)
        comments_list = top5["text"].astype(str).tolist()

        # representative comment: try clusters.json mapping
        rep = None
        if str(cid) in clusters_map and clusters_map[str(cid)].get("representative_comments"):
            rep_info = clusters_map[str(cid)]["representative_comments"][0]
            rep_idx = int(rep_info.get("index", -1))
            if rep_idx >= 0 and rep_idx < len(df):
                rep = str(df.iloc[rep_idx]["text"])
        if not rep:
            rep = comments_list[0]

        # ensure rep included (if not already in top5)
        if rep not in comments_list:
            comments_list = [rep] + comments_list[:4]

        prompt = build_prompt(comments_list)

        # call model (try python ollama client first)
        output = None
        model_text = None
        try:
            # try Ollama Python package if present; capture python errors for debugging
            try:
                import ollama
                try:
                    # use the chat helper with minimal args; ollama.chat controls options via `format`/`options`
                    resp = ollama.chat(
                        model=MODEL_NAME,
                        format="json",
                        messages=[{"role": "user", "content": prompt}],
                    )
                    # resp may be a data structure or ChatResponse object; stringify safely
                    if isinstance(resp, (dict, list)):
                        model_text = json.dumps(resp, ensure_ascii=False)
                    else:
                        # prefer the assistant message content if available
                        model_text = None
                        if hasattr(resp, "message") and getattr(resp, "message") is not None:
                            try:
                                model_text = getattr(resp.message, "content", None)
                            except Exception:
                                model_text = None
                        if model_text is None:
                            model_text = str(resp)
                except Exception as e_chat:
                    # record chat error and fall back to CLI
                    model_text = f"PYTHON_OLLAMA_CHAT_ERROR:\n{str(e_chat)}\nFALLING_BACK_TO_CLI"
                    model_text = call_ollama_cli(prompt, TEMPERATURE, MAX_NEW_TOKENS, TOP_P)
            except Exception as e_import:
                # python ollama not usable; note error and fallback to CLI
                model_text = f"PYTHON_OLLAMA_IMPORT_ERROR:\n{str(e_import)}"
                model_text = model_text + "\nFALLING_BACK_TO_CLI"
                model_text = call_ollama_cli(prompt, TEMPERATURE, MAX_NEW_TOKENS, TOP_P)

        except Exception as e:
            # unexpected outer error
            print(f"Model call failed for cluster {cid}: {e}")
            model_text = f"UNEXPECTED_ERROR:\n{str(e)}"

        # Save raw model output for debugging
        try:
            dbg_path = f"debug_output_cluster_{cid}.txt"
            with open(dbg_path, "w", encoding="utf-8") as dbg_f:
                dbg_f.write(str(model_text or ""))
        except Exception:
            pass

        parsed = parse_model_output(model_text or "")
        if parsed is None:
            print(f"Cluster {cid}: first parse failed, retrying with lower temperature")
            # retry once with lower temp
            try:
                model_text = call_ollama_cli(prompt, 0.2, MAX_NEW_TOKENS, TOP_P)
            except Exception:
                model_text = ""
            parsed = parse_model_output(model_text or "")

        if parsed is None:
            print(f"Cluster {cid}: failed to parse JSON from model output; saving minimal placeholder")
            entry = {
                "cluster_id": cid,
                "demand_score": float(demand),
                "cluster_title": "",
                "pain_point": "",
                "video_outline": {"hook": "", "body": "", "cta": ""},
            }
        else:
            # basic validation and trimming
            title = str(parsed.get("cluster_title", "")).strip()
            # enforce max 4 words
            if len(title.split()) > 4:
                title = " ".join(title.split()[:4])
            pain = str(parsed.get("pain_point", "")).strip()
            vo = parsed.get("video_outline", {})
            hook = str(vo.get("hook", "")).strip()
            body = str(vo.get("body", "")).strip()
            cta = str(vo.get("cta", "")).strip()

            entry = {
                "cluster_id": cid,
                "demand_score": float(demand),
                "cluster_title": title,
                "pain_point": pain,
                "video_outline": {"hook": hook, "body": body, "cta": cta},
            }

        results.append(entry)
        # small delay to avoid overloading local model
        time.sleep(0.3)

    # write results
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"Wrote {len(results)} cluster insights to {OUT_JSON}")


if __name__ == "__main__":
    main()
