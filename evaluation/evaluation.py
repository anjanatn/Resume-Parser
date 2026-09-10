"""
evaluation.py — Precision@K / Recall evaluation for the Resume Parser & Search Engine.

Usage:
    python evaluation/evaluation.py

Outputs:
    - Precision@5 for each query
    - Recall@10 for each query
    - Average parsing accuracy metrics
"""

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.parser import ResumeParser
from src.search_engine import IntelligentSearchEngine

# ─────────────────────── GROUND TRUTH DEFINITIONS ─────────────────────────────
#
# Format: each query maps to a list of candidate name substrings that are
# considered "relevant" for that query. These are manually labelled ground truths.
#
QUERY_GROUND_TRUTHS = {
    "Python developers with 3+ years experience": [
        "Alex Chen", "Maria Garcia", "Marcus Johnson"
    ],
    "DevOps engineer AWS Kubernetes Terraform": [
        "Priya Sharma", "David Kim"
    ],
    "Data Scientist PyTorch NLP PhD": [
        "Marcus Johnson"
    ],
    "Full-Stack Python React Developer": [
        "Alex Chen", "Elena Rostova"
    ],
    "Senior Backend Engineer FastAPI Docker": [
        "Alex Chen", "Maria Garcia"
    ],
}

SAMPLE_JD = """
Senior Backend Engineer – Python & Cloud Infrastructure

We are looking for a Senior Software Engineer with 3+ years of hands-on experience
in Python (FastAPI or Django), Docker, Kubernetes, and AWS.

Required:
- Bachelor's degree in Computer Science or related field
- Experience with CI/CD pipelines and microservices architecture
- Proficiency in PostgreSQL and Redis

Nice to have:
- Machine Learning integration experience
- Terraform infrastructure-as-code
"""


# ─────────────────────────── METRIC HELPERS ──────────────────────────────────

def precision_at_k(results, relevant_names, k=5):
    """
    Precision@K = (relevant candidates in top-K) / K
    """
    top_k = results[:k]
    hits = sum(
        1 for r in top_k
        if any(rel.lower() in r["candidate"]["name"].lower() for rel in relevant_names)
    )
    return hits / min(k, len(top_k)) if top_k else 0.0


def recall_at_k(results, relevant_names, k=10):
    """
    Recall@K = (relevant candidates in top-K) / total relevant
    """
    if not relevant_names:
        return 0.0
    top_k = results[:k]
    hits = sum(
        1 for rel in relevant_names
        if any(rel.lower() in r["candidate"]["name"].lower() for r in top_k)
    )
    return hits / len(relevant_names)


def mean_reciprocal_rank(results, relevant_names):
    """
    MRR = 1 / rank_of_first_relevant_result
    """
    for rank, r in enumerate(results, start=1):
        if any(rel.lower() in r["candidate"]["name"].lower() for rel in relevant_names):
            return 1.0 / rank
    return 0.0


# ─────────────────────────── MAIN EVALUATION ─────────────────────────────────

def run_evaluation(candidates):
    """Run full evaluation suite on parsed candidate list."""

    engine = IntelligentSearchEngine(candidates)
    print("\n" + "=" * 70)
    print("  RESUME PARSER & SEARCH ENGINE — EVALUATION REPORT")
    print("=" * 70)

    # ── 1. Search Quality Metrics ──────────────────────────────────────────
    print("\n[1] SEARCH QUALITY METRICS\n")
    print(f"  {'Query':<45} {'P@5':>6} {'R@10':>6} {'MRR':>6}")
    print(f"  {'-'*45} {'-----':>6} {'-----':>6} {'-----':>6}")

    p5_list, r10_list, mrr_list = [], [], []

    for query, relevant in QUERY_GROUND_TRUTHS.items():
        results = engine.search(query=query)
        p5  = precision_at_k(results, relevant, k=5)
        r10 = recall_at_k(results, relevant, k=10)
        mrr = mean_reciprocal_rank(results, relevant)
        p5_list.append(p5); r10_list.append(r10); mrr_list.append(mrr)
        label = query[:43] + ".." if len(query) > 45 else query
        print(f"  {label:<45} {p5:>6.2f} {r10:>6.2f} {mrr:>6.2f}")

    avg_p5  = sum(p5_list)  / len(p5_list)
    avg_r10 = sum(r10_list) / len(r10_list)
    avg_mrr = sum(mrr_list) / len(mrr_list)
    print(f"\n  {'AVERAGES':<45} {avg_p5:>6.2f} {avg_r10:>6.2f} {avg_mrr:>6.2f}")

    # ── 2. JD Matching Quality ─────────────────────────────────────────────
    print("\n[2] JD AUTO-MATCHER — TOP 5 RESULTS\n")
    jd_data = engine.match_job_description(SAMPLE_JD)
    req = jd_data["jd_requirements"]
    print(f"  Extracted Skills : {', '.join(req['skills']) or 'None'}")
    print(f"  Min Experience   : {req['min_exp']} yrs")
    print(f"  Min Degree       : {req['min_degree']}")
    print()
    print(f"  {'Rank':<5} {'Candidate':<25} {'Score':>7} {'Matched Skills'}")
    print(f"  {'-'*5} {'-'*25} {'-'*7} {'-'*25}")
    for i, r in enumerate(jd_data["results"][:5], 1):
        c = r["candidate"]
        matched = ", ".join(r["match_details"]["matched_skills"][:4])
        print(f"  #{i:<4} {c['name']:<25} {r['suitability_score']:>6.1f}%  {matched}")

    # ── 3. Parsing Accuracy ────────────────────────────────────────────────
    print("\n[3] PARSING ACCURACY REPORT\n")
    total = len(candidates)
    has_email  = sum(1 for c in candidates if c["contact"]["email"] != "N/A")
    has_phone  = sum(1 for c in candidates if c["contact"]["phone"] != "N/A")
    has_skills = sum(1 for c in candidates if len(c["skills"]) > 0)
    has_degree = sum(1 for c in candidates if c["highest_degree"] != "None")
    has_exp    = sum(1 for c in candidates if c["experience_years"] > 0)

    metrics = [
        ("Email Extraction",     has_email,  total),
        ("Phone Extraction",     has_phone,  total),
        ("Skills Extraction",    has_skills, total),
        ("Degree Detection",     has_degree, total),
        ("Experience Parsing",   has_exp,    total),
    ]
    for name, found, tot in metrics:
        pct = (found / tot * 100) if tot else 0
        bar = "#" * int(pct / 5)
        print(f"  {name:<25} {found:>2}/{tot}  [{bar:<20}] {pct:.0f}%")

    # ── 4. Per-Candidate Summary ───────────────────────────────────────────
    print("\n[4] CANDIDATE PARSE SUMMARY\n")
    print(f"  {'#':<3} {'Name':<30} {'Exp':>5} {'Degree':<12} {'Skills':>6} {'Email':>10}")
    print(f"  {'-'*3} {'-'*30} {'-'*5} {'-'*12} {'-'*6} {'-'*10}")
    for i, c in enumerate(candidates, 1):
        email_ok = "Yes" if c["contact"]["email"] != "N/A" else "No"
        print(
            f"  {i:<3} {c['name'][:29]:<30} {c['experience_years']:>5} "
            f"{c['highest_degree']:<12} {len(c['skills']):>6} {email_ok:>10}"
        )

    # ── 5. Sample Queries & Expected Outputs ──────────────────────────────
    print("\n[5] SAMPLE QUERIES & TOP RANKED RESULTS\n")
    for query in list(QUERY_GROUND_TRUTHS.keys())[:3]:
        results = engine.search(query=query)
        print(f"  Query : \"{query}\"")
        for i, r in enumerate(results[:3], 1):
            c = r["candidate"]
            explanation = r.get("ranking_explanation", [])
            first_reason = explanation[0] if explanation else ""
            print(f"    #{i}. {c['name']:<25} {r['suitability_score']:>6.1f}%  {first_reason}")
        print()

    print("=" * 70)
    print("  Evaluation complete.")
    print("=" * 70 + "\n")

    return {
        "avg_precision_at_5": round(avg_p5, 3),
        "avg_recall_at_10": round(avg_r10, 3),
        "avg_mrr": round(avg_mrr, 3),
        "parsing_accuracy": {
            "email_pct": round(has_email / total * 100, 1),
            "phone_pct": round(has_phone / total * 100, 1),
            "skills_pct": round(has_skills / total * 100, 1),
            "degree_pct": round(has_degree / total * 100, 1),
        }
    }


if __name__ == "__main__":
    # Load real resumes from ResumeParserUnlocked/ for evaluation
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    unlock_dir = os.path.join(BASE_DIR, "ResumeParserUnlocked")
    data_dir   = os.path.join(BASE_DIR, "data", "resumes")

    parser = ResumeParser()
    candidates = []

    for d in [data_dir, unlock_dir]:
        if os.path.exists(d):
            for fname in sorted(os.listdir(d)):
                if fname.lower().endswith((".pdf", ".docx", ".txt")) and not fname.startswith("._"):
                    try:
                        c = parser.parse(os.path.join(d, fname), filename=fname)
                        candidates.append(c)
                    except Exception as e:
                        print(f"[WARN] Skipped {fname}: {e}")

    if not candidates:
        print("No candidates found. Generate synthetic resumes first: python src/generator.py")
        sys.exit(1)

    print(f"\nLoaded {len(candidates)} candidate(s) for evaluation.")
    run_evaluation(candidates)
