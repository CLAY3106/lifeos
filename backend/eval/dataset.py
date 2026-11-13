"""
Retrieval eval dataset: one realistic student's month, plus labeled queries.

Every entity has a stable key ("a_linalg_ps7", "j_stripe", ...). Each query
lists the keys a good retriever must return. Queries are tagged by type so the
eval shows where each search method wins:

- lexical:  the query shares exact words with the target (names, codes, numbers).
            Keyword search should do well here.
- semantic: the query paraphrases the target with different words
            ("food" -> "ramen", "exam" -> "midterm"). Vector search should win.
- mixed:    some shared words, some paraphrase, often several targets.

Dates are fixed so chunk text (e.g. "due Nov 12") is identical on every run.
"""

from datetime import date, datetime

ASSIGNMENTS = {
    "a_linalg_ps7": dict(title="Linear Algebra Problem Set 7", course="MATH 240", due=datetime(2026, 11, 6), hours=3, status="pending"),
    "a_linalg_midterm": dict(title="Linear Algebra Midterm", course="MATH 240", due=datetime(2026, 11, 13), hours=6, status="pending"),
    "a_os_lab3": dict(title="Operating Systems Lab 3: Scheduler", course="COMP 315", due=datetime(2026, 11, 9), hours=5, status="pending"),
    "a_os_reading": dict(title="Read OSTEP chapters 7-9", course="COMP 315", due=datetime(2026, 11, 5), hours=2, status="done"),
    "a_japanese_kanji": dict(title="Kanji quiz lessons 12-14", course="JAPN 203", due=datetime(2026, 11, 7), hours=1.5, status="pending"),
    "a_japanese_essay": dict(title="Japanese composition: my hometown", course="JAPN 203", due=datetime(2026, 11, 18), hours=3, status="pending"),
    "a_parallel_hw": dict(title="OpenMP matrix multiply homework", course="COMP 481", due=datetime(2026, 11, 10), hours=4, status="pending"),
    "a_parallel_proj": dict(title="Parallel computing final project proposal", course="COMP 481", due=datetime(2026, 11, 20), hours=5, status="pending"),
    "a_stats_ps": dict(title="Probability homework 5: Bayes rule", course="MATH 260", due=datetime(2026, 10, 30), hours=2, status="overdue"),
    "a_seminar": dict(title="Career seminar reflection paper", course="SEMN 200", due=datetime(2026, 11, 4), hours=1, status="done"),
}

JOBS = {
    "j_stripe": dict(company="Stripe", role="Software Engineer Intern", applied=date(2026, 10, 12), status="oa", location="Seattle", notes="HackerRank online assessment due Nov 8"),
    "j_google": dict(company="Google", role="STEP Intern", applied=date(2026, 10, 3), status="interview_scheduled", location="Mountain View", notes="Technical phone screen Nov 11, practice graphs and DP"),
    "j_meta": dict(company="Meta", role="Software Engineer Intern", applied=date(2026, 10, 9), status="applied", location="Menlo Park", notes="Referred by alum Chau"),
    "j_amazon": dict(company="Amazon", role="SDE Intern", applied=date(2026, 9, 28), status="rejected", location="Seattle", notes="Rejected after OA"),
    "j_doordash": dict(company="DoorDash", role="Backend Engineering Intern", applied=date(2026, 10, 20), status="applied", location="San Francisco", notes="Referral from Mai"),
    "j_coinbase": dict(company="Coinbase", role="Software Engineer Intern", applied=date(2026, 10, 25), status="applied", location="Remote", notes="Follow up with recruiter next week"),
    "j_gm": dict(company="General Motors", role="Software Developer Intern", applied=date(2026, 10, 15), status="oa", location="Detroit", notes="Coding challenge on Codility"),
    "j_rakuten": dict(company="Rakuten", role="Backend Intern", applied=date(2026, 10, 18), status="offer", location="Tokyo", notes="Offer received, decide by Nov 30"),
}

EXPENSES = {
    "e_ramen": dict(amount=11.5, category="food", note="ramen at Ichiran", spent=datetime(2026, 11, 1), group="wants"),
    "e_groceries": dict(amount=42.3, category="food", note="weekly groceries at Life supermarket", spent=datetime(2026, 11, 2), group="needs"),
    "e_konbini": dict(amount=6.2, category="food", note="onigiri and coffee at 7-Eleven", spent=datetime(2026, 11, 3), group="wants"),
    "e_suica": dict(amount=30.0, category="transport", note="Suica card top-up", spent=datetime(2026, 11, 1), group="needs"),
    "e_shinkansen": dict(amount=95.0, category="transport", note="Shinkansen ticket to Kyoto", spent=datetime(2026, 10, 24), group="wants"),
    "e_textbook": dict(amount=58.0, category="study", note="OSTEP printed textbook", spent=datetime(2026, 10, 20), group="needs"),
    "e_leetcode": dict(amount=35.0, category="study", note="LeetCode premium subscription", spent=datetime(2026, 10, 15), group="wants"),
    "e_gym": dict(amount=40.0, category="fitness", note="Anytime Fitness monthly membership", spent=datetime(2026, 11, 1), group="needs"),
    "e_shoes": dict(amount=85.0, category="fitness", note="new running shoes", spent=datetime(2026, 10, 28), group="wants"),
    "e_karaoke": dict(amount=18.0, category="other", note="karaoke night with exchange friends", spent=datetime(2026, 10, 31), group="wants"),
    "e_phone": dict(amount=25.0, category="other", note="mobile phone plan", spent=datetime(2026, 11, 1), group="needs"),
    "e_savings": dict(amount=100.0, category="other", note="transfer to emergency fund", spent=datetime(2026, 11, 1), group="savings"),
}

WORKOUTS = {
    "w_push": dict(type="push", mins=60, notes="bench press 3x8, overhead press, dips"),
    "w_pull": dict(type="pull", mins=55, notes="deadlift 3x5, pull-ups, barbell rows"),
    "w_legs": dict(type="legs", mins=65, notes="squats 4x6, lunges, calf raises"),
    "w_run": dict(type="cardio", mins=35, notes="5k run along the Imperial Palace loop"),
    "w_soccer": dict(type="soccer", mins=90, notes="pickup futsal with Sophia friends"),
    "w_yoga": dict(type="mobility", mins=20, notes="stretching and yoga for lower back"),
}

QUERIES = [
    # --- lexical: exact names, codes, terms ---------------------------------
    dict(q="MATH 240", type="lexical", relevant=["a_linalg_ps7", "a_linalg_midterm"]),
    dict(q="Stripe", type="lexical", relevant=["j_stripe"]),
    dict(q="COMP 315 scheduler lab", type="lexical", relevant=["a_os_lab3"]),
    dict(q="Suica", type="lexical", relevant=["e_suica"]),
    dict(q="deadlift", type="lexical", relevant=["w_pull"]),
    dict(q="Rakuten offer", type="lexical", relevant=["j_rakuten"]),
    dict(q="OpenMP", type="lexical", relevant=["a_parallel_hw"]),
    dict(q="Codility coding challenge", type="lexical", relevant=["j_gm"]),
    dict(q="LeetCode", type="lexical", relevant=["e_leetcode"]),
    dict(q="kanji quiz", type="lexical", relevant=["a_japanese_kanji"]),

    # --- semantic: paraphrase, no shared keywords ---------------------------
    dict(q="how much did I spend eating out", type="semantic", relevant=["e_ramen", "e_konbini"]),
    dict(q="train and subway costs", type="semantic", relevant=["e_suica", "e_shinkansen"]),
    dict(q="upper body strength training", type="semantic", relevant=["w_push", "w_pull"]),
    dict(q="leg day", type="semantic", relevant=["w_legs"]),
    dict(q="companies that turned me down", type="semantic", relevant=["j_amazon"]),
    dict(q="exam preparation", type="semantic", relevant=["a_linalg_midterm", "a_japanese_kanji"]),
    dict(q="language class work", type="semantic", relevant=["a_japanese_kanji", "a_japanese_essay"]),
    dict(q="money I put aside", type="semantic", relevant=["e_savings"]),
    dict(q="gym subscription", type="semantic", relevant=["e_gym"]),
    dict(q="evening out with friends", type="semantic", relevant=["e_karaoke"]),

    # --- mixed: partial overlap, often multiple targets ---------------------
    dict(q="online assessments I still need to take", type="mixed", relevant=["j_stripe", "j_gm"]),
    dict(q="upcoming interviews", type="mixed", relevant=["j_google"]),
    dict(q="applications that came through a referral", type="mixed", relevant=["j_meta", "j_doordash"]),
    dict(q="overdue homework", type="mixed", relevant=["a_stats_ps"]),
    dict(q="parallel computing assignments", type="mixed", relevant=["a_parallel_hw", "a_parallel_proj"]),
    dict(q="running and cardio", type="mixed", relevant=["w_run"]),
    dict(q="operating systems textbook", type="mixed", relevant=["e_textbook", "a_os_reading"]),
    dict(q="internships in Seattle", type="mixed", relevant=["j_stripe", "j_amazon"]),
    dict(q="playing football", type="mixed", relevant=["w_soccer"]),
    dict(q="recruiter follow-ups", type="mixed", relevant=["j_coinbase"]),
]
