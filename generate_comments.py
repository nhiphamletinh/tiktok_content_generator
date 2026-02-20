#!/usr/bin/env python3
"""
Generate ~200 synthetic TikTok-style comments for an education niche (study abroad & scholarships)
Saves to comments.csv with columns: comment_id,text,like_count
"""
import csv
import random
import itertools
import textwrap

random.seed(42)

NUM_COMMENTS = 200
CLUSTERS = 5
PER_CLUSTER = NUM_COMMENTS // CLUSTERS  # 40

# Helpers to produce informal, TikTok-style phrasing
def pick(choices):
    return random.choice(choices)

def maybe_emote():
    return pick(["", " 😊", " 🙏", " 😭", " 😅", " 🤔", "🔥"]).strip()

# Templates / phrase banks per cluster
cluster_templates = {
    "A": [
        # Scholarship Eligibility (GPA, IELTS/TOEFL, major, financial background)
        "Is 3.2 GPA enough for this scholarship?",
        "Minimum GPA for this?",
        "Can someone with average grades still get it?",
        "Be honest, is 3.0 too low?",
        "Do they check IELTS scores or just GPA?",
        "TOEFL vs IELTS — which matters more here?",
        "My major isn't related, can I still apply?",
        "Is this only for STEM majors?",
        "Do they look at family income or just merit?",
        "Do scholarships accept transfer students?",
        "Low-income students have a shot?",
        "Any idea about age limits for applicants?",
        "Does the country require a specific major?",
        "If I have a 2.9 GPA but great essays—any hope?",
        "How strict are they about transcripts?",
        "Can community college students apply?",
        "Is international undergraduate eligible or only masters?",
        "Is there any quota for countries?",
        "What if my IELTS is 6.0 only?",
        "Does retaking exams help?",
    ],
    "B": [
        # Application Timeline
        "When should I start preparing?",
        "Deadline for this is when?",
        "Is it rolling admission or a fixed deadline?",
        "Should I apply this year or next year?",
        "How early do I need to gather docs?",
        "Does anyone know if deadlines vary by nationality?",
        "When do they usually notify winners?",
        "How long after application do they interview?",
        "Is it dumb to start application 2 months before deadline?",
        "How many months in advance did you prepare?",
        "When do schools open applications for 2026?",
        "Last-minute applicants—worth a try?",
        "If I miss the fall deadline, is spring possible?",
        "Is gap year okay before applying?",
        "Tips for speeding up the timeline?",
        "Do references take a long time to get?",
        "When should I book TOEFL/IELTS to meet deadlines?",
        "How early should I ask professors for rec letters?",
        "Does anyone else panic about deadlines?",
        "Is 1 month enough to finish SOP + recs?",
    ],
    "C": [
        # Personal Statement / Essays
        "How do I write an SOP that stands out?",
        "What should I include in my personal statement?",
        "How long should the SOP be?",
        "Example template for scholarship essay pls?",
        "Can I use personal hardships in my essay?",
        "Do they like stories or achievements more?",
        "Should I mention my volunteer work?",
        "Any short sample lines for opening the SOP?",
        "How honest should I be about weaknesses?",
        "Should I avoid cliches like 'ever since I was a child'?",
        "Do they value creativity over formal tone?",
        "Is it okay to be emotional in SOP?",
        "How many drafts do people normally write?",
        "Do they check for AI-written essays?",
        "Any quick checklist for final proofread?",
        "What templates have actually worked for you?",
        "Is it ok to use bullet lists in statement?",
        "How much research to show about the program?",
        "Can I reuse the same essay for multiple scholarships?",
        "How do I explain a gap year in SOP?",
    ],
    "D": [
        # Visa / Interview Process
        "How hard is the visa interview for students?",
        "What questions do embassies usually ask?",
        "Do they ask about bank statements in detail?",
        "Visa approval rate for scholarship students?",
        "How to prepare for embassy interview?",
        "Should I carry original docs or copies?",
        "Do interviewers ask about return plans?",
        "How long is the visa processing typically?",
        "Any tips for answering financial proof questions?",
        "Do they ever ask about roommates/where you'll stay?",
        "Practice Qs for a student visa interview?",
        "Has anyone been denied despite scholarship?",
        "What if embassy asks why this uni over local options?",
        "Do they look up your social media?",
        "Do you need certified translations for docs?",
        "How honest should I be about future plans?",
        "Got advice for stressed interviewees?",
        "What to do if visa delayed after acceptance?",
        "Is it common to get additional requests after interview?",
        "Do they check scholarship award letters carefully?",
    ],
    "E": [
        # Financial Planning / Cost
        "How much is living cost there monthly?",
        "Is full scholarship really full?",
        "Part-time work allowed on scholarship?",
        "Tuition fees for international students—any estimates?",
        "How to budget as a student abroad?",
        "Are there hidden fees I should watch for?",
        "How to find cheap housing near campus?",
        "Can scholarships cover living expenses?",
        "How much bank balance do they want for visa?",
        "Any tips to save on food & transport?",
        "Is it realistic to survive on a partial scholarship?",
        "How to manage money if scholarship pays monthly?",
        "Do students usually get paid internships?",
        "Are emergency funds required by the uni?",
        "How to plan if tuition is only partially covered?",
        "What are the cheapest cities for students?",
        "Do scholarship offers ever include travel grants?",
        "How to apply for additional grants later?",
        "Is student health insurance expensive?",
        "Tips for currency exchange savings?",
    ],
}

# Variation utilities
openers = [
    "Hey guys", "Quick Q", "Real talk", "Serious question", "Low-key curious", "Anyone know", "PSA", "Confused", "Genuinely asking",
]
mid_phrases = [
    "I was thinking...", "this is stressing me out", "pls help", "drop your experiences", "need advice", "is this normal?",
]

# Like count distributions: clusters A and B should have slightly higher average
def sample_like_count(cluster_key):
    if cluster_key in ("A", "B"):
        # higher average: use skewed distribution
        return max(0, int(random.gauss(12, 8)))  # mean ~12, sd 8
    else:
        return max(0, int(random.gauss(6, 5)))  # mean ~6, sd 5

# Compose comments
comments = []
comment_id = 1

for cluster_key, templates in cluster_templates.items():
    for i in range(PER_CLUSTER):
        # pick a template
        base = pick(templates)

        # Decide style variations
        style = random.random()
        # 20% chance to prepend opener
        if style < 0.2:
            prefix = pick(openers) + ": "
        elif style < 0.35:
            prefix = pick(openers) + " — "
        else:
            prefix = ""

        # 30% chance to append mid phrase or emote
        if random.random() < 0.3:
            suffix = " " + pick(mid_phrases)
        else:
            suffix = maybe_emote()

        # 15% chance to make it longer by adding an extra sentence
        extra = ""
        if random.random() < 0.15:
            extra_sent = pick([
                "Also, any quick resources to read?",
                "Would love to see examples if you have them.",
                "Feeling lowkey stressed about this timeline.",
                "If someone has links, drop them pls.",
                "Not sure where to start tbh.",
            ])
            extra = " " + extra_sent

        # 10% chance to rephrase slightly
        if random.random() < 0.1:
            # swap some words
            base = base.replace("scholarship", pick(["the scholarship", "this scholarship", "that grant"]))

        # Ensure many have question marks where appropriate: if base doesn't end with '?', maybe add one for emphasis
        text = prefix + base + suffix + extra

        # small random punctuation edits to imitate informal style
        if random.random() < 0.08:
            text = text + "!!"
        if random.random() < 0.05 and not text.endswith("?"):
            text = text + "?"

        # Vary casing slightly
        if random.random() < 0.05:
            text = text.upper()

        like_count = sample_like_count(cluster_key)

        comments.append((comment_id, text, like_count))
        comment_id += 1

# If NUM_COMMENTS is not exactly matched (in case of integer division), add leftovers randomly
while len(comments) < NUM_COMMENTS:
    cluster_key = pick(list(cluster_templates.keys()))
    base = pick(cluster_templates[cluster_key])
    text = base + maybe_emote()
    like_count = sample_like_count(cluster_key)
    comments.append((comment_id, text, like_count))
    comment_id += 1

# Shuffle comments slightly to avoid perfect cluster blocks
random.shuffle(comments)

# Save to CSV
with open("comments.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["comment_id", "text", "like_count"])
    for cid, text, likes in comments:
        writer.writerow([cid, text, likes])

print(f"Wrote {len(comments)} comments to comments.csv")
