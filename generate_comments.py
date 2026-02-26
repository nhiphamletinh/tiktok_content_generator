#!/usr/bin/env python3
"""
Generate ~200 synthetic TikTok-style comments for an education niche (study abroad & scholarships)
Saves to comments.csv with columns: comment_id,text,like_count
"""
import csv
import random
import itertools
import textwrap

random.seed(2026)

NUM_COMMENTS = 200
CLUSTERS = 5
PER_CLUSTER = NUM_COMMENTS // CLUSTERS  # 40

# Helpers
def pick(choices):
    return random.choice(choices)

def sample_like_count(cluster_key):
    # clusters A and B slightly higher average likes
    if cluster_key in ("A", "B"):
        return max(0, int(random.gauss(14, 9)))
    return max(0, int(random.gauss(6, 6)))

def maybe_emote():
    return pick(["", " 😊", " 🙏", " 😭", " 😅", " 🤔", "🔥", "✨"]).strip()


def inject_typo(s: str, prob=0.15) -> str:
    # Randomly introduce a simple typo: drop a char, swap adjacent, or duplicate
    if random.random() > prob or len(s) < 4:
        return s
    i = random.randrange(len(s) - 1)
    op = random.choice(["drop", "swap", "dup", "replace"])
    lst = list(s)
    if op == "drop":
        del lst[i]
    elif op == "swap":
        lst[i], lst[i + 1] = lst[i + 1], lst[i]
    elif op == "dup":
        lst.insert(i, lst[i])
    else:
        lst[i] = random.choice(list("aeiouy"))
    return "".join(lst)


def slangify(s: str) -> str:
    # add slang/abbrev occasionally
    if random.random() < 0.25:
        s = s.replace("please", "pls").replace("please", "plz")
        s = s.replace("you", "u").replace("your", "ur")
        s = s.replace("application", "app")
    # sometimes add filler interjection
    if random.random() < 0.12:
        s = pick(["lol ", "ngl ", "fr ", "tbh, "]) + s
    return s


# Synonym maps and paraphrase slots to increase variety
SYN = {
    "like": ["like", "prefer", "value", "care about"],
    "stories": ["stories", "personal stories", "life stories", "anecdotes"],
    "achievements": ["achievements", "accomplishments", "wins", "awards"],
    "gpa": ["GPA", "grade average", "GPA (scale)", "grades"],
    "deadline": ["deadline", "due date", "cutoff", "final date"],
    "apply": ["apply", "submit an app", "send my application", "put in my application"],
}


# Build highly-varied generation using fragments and templates

# Phrase fragments per topic to assemble diverse sentences
FRAGMENTS = {
    "A": {
        "intros": ["any idea", "quick q", "real talk", "serious q", "low-key wondering"],
        "asks": [
            "what's the minimum {gpa} they're asking for",
            "would a {gpa} of {val} be ok",
            "can someone with average {gpa} still get a schlrshp",
            "do they care more about {gpa} or essays",
            "is it limited to STEM peeps",
            "do they check financial background or nah",
        ],
        "closers": ["any experiences?", "pls lemme know", "thx in advance", "help pls", "ngl, stressed"],
    },
    "B": {
        "intros": ["deadline q", "when do i start", "timeline q", "serious question"],
        "asks": [
            "when's the {deadline} for this",
            "is it rolling or fixed cutoff",
            "if i miss fall can i do spring intake",
            "how early to book tests to meet the due date",
            "is 1 month enough to finish SOP+recs",
        ],
        "closers": ["any tips?", "pls advice", "anyone done this?", "tfw panicking"],
    },
    "C": {
        "intros": ["essay q", "sop help", "writing q", "pls help"],
        "asks": [
            "how to open my sop without sounding basic",
            "should i flex achievements or tell stories",
            "can i include personal hardships without sounding dramatic",
            "how long should the personal statement be",
            "do they frown on AI-assisted drafts",
        ],
        "closers": ["examples pls", "templates?", "thx 🙏", "any sample lines?"],
    },
    "D": {
        "intros": ["visa q", "embassy tips", "interview q"],
        "asks": [
            "what q's do they ask at the embassy",
            "do i need original bank docs or copies",
            "how long does the visa take",
            "do they ask about return plans or jobs",
            "will scholarship affect approval chances",
        ],
        "closers": ["rly need this info", "pls share experiences", "anyone?"],
    },
    "E": {
        "intros": ["money q", "cost q", "budget q"],
        "asks": [
            "how much do ppl spend on living there monthly",
            "does the scholarship cover living costs",
            "can i work part time while on this grant",
            "what's a realistic monthly budget for students",
            "do uni fees include health insurance",
        ],
        "closers": ["pls share #s", "any hacks?", "tipz?", "thx!"]
    },
}


def assemble_comment_for_cluster(cluster_key: str) -> str:
    fr = FRAGMENTS[cluster_key]
    structure = random.choices(["short_q", "full_q", "multi", "fragment"], weights=[30, 40, 18, 12])[0]
    def slot_replace(tpl: str):
        return tpl.format(
            gpa=pick(SYN["gpa"]),
            val=pick(["3.2", "3.0", "2.8", "3.5", "2.5"]),
            deadline=pick(SYN["deadline"]),
        )

    if structure == "short_q":
        s = pick(fr["intros"]) + ": " + slot_replace(pick(fr["asks"]))
    elif structure == "full_q":
        s = f"{pick(fr['intros']).capitalize()} — {slot_replace(pick(fr['asks']))}, {pick(fr['closers'])}"
    elif structure == "multi":
        part1 = slot_replace(pick(fr["asks"]))
        part2 = slot_replace(pick(fr["asks"]))
        s = f"{pick(fr['intros']).capitalize()}: {part1} / {part2} {pick(fr['closers'])}"
    else:
        s = slot_replace(pick(fr["asks"])) + " " + pick(fr["closers"]) 

    # Add paraphrase variety: move clauses, contraction, slang, code-switch
    if random.random() < 0.2:
        s = s.replace("can i", "can I")
    if random.random() < 0.18:
        s = s.replace("please", "pls")
    if random.random() < 0.12:
        s = pick(["lol ", "ngl ", "tbh "]) + s
    if random.random() < 0.08:
        s = s + " " + pick(["#studyabroad", "#scholarship", "@uni"])
    # code-switch small bits
    if random.random() < 0.06:
        s = s + pick([" ¿alguien sabe?", " alguien?", " gracias"])
    # random emoji positions
    if random.random() < 0.5:
        if random.random() < 0.5:
            s = maybe_emote() + " " + s
        else:
            s = s + maybe_emote()
    # punctuation and typos
    if random.random() < 0.14:
        s = inject_typo(s, prob=0.22)
    if random.random() < 0.07:
        s = s.upper()
    # clean spacing
    s = " ".join(s.split())
    return s


def mutate_sentence(s: str) -> str:
    # Apply a few small transformations to diversify phrasing
    # 1) maybe rephrase as a polite request
    if random.random() < 0.12:
        s = "pls " + s
    # 2) maybe move clause to front/back
    if random.random() < 0.12 and "," in s:
        parts = s.split(",")
        random.shuffle(parts)
        s = ",".join(parts)
    # 3) sometimes add filler or hesitation
    if random.random() < 0.18:
        s = s + " " + pick(["idk", "tbh", "ngl", "anyone?", "help pls"]) 
    # 4) random contraction and punctuation changes
    if random.random() < 0.2:
        s = s.replace("do not", "don't").replace("cannot", "can't")
    # 5) slang and typos
    s = slangify(s)
    s = inject_typo(s, prob=0.12)
    # 6) random emoji
    if random.random() < 0.45:
        s = s + maybe_emote()
    return s


# Generate without exact duplicates by tracking normalized text
seen = set()
comments = []
cid = 1

cluster_keys = ["A", "B", "C", "D", "E"]
for cluster_key in cluster_keys:
    attempts = 0
    produced = 0
    while produced < PER_CLUSTER:
        attempts += 1
        text = assemble_comment_for_cluster(cluster_key)
        # normalize for duplicate checking
        norm = " ".join(text.lower().split())
        if norm in seen:
            # perturb if duplicate
            text = text + " " + pick(["pls", "anyone?", "?", "...", "ngl"]) 
            norm = " ".join(text.lower().split())
            if norm in seen:
                text = inject_typo(text, prob=0.35)
                norm = " ".join(text.lower().split())
                if norm in seen:
                    if attempts > PER_CLUSTER * 10:
                        break
                    continue

        seen.add(norm)
        likes = sample_like_count(cluster_key)
        comments.append((cid, text, likes))
        cid += 1
        produced += 1

# If any rounding/shortage, fill randomly using assembler
while len(comments) < NUM_COMMENTS:
    k = pick(cluster_keys)
    t = assemble_comment_for_cluster(k)
    norm = " ".join(t.lower().split())
    if norm in seen:
        t = t + " " + pick(["pls", "anyone?", "?", "...", "ngl"]) 
        norm = " ".join(t.lower().split())
    seen.add(norm)
    comments.append((cid, t, sample_like_count(k)))
    cid += 1

random.shuffle(comments)

# Save to CSV
with open("comments.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["comment_id", "text", "like_count"])
    for cid_val, text, likes in comments:
        writer.writerow([cid_val, text, likes])

print(f"Wrote {len(comments)} comments to comments.csv")
