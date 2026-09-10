import os
import sys
import json

# Ensure UTF-8 output encoding for Windows terminal
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from src.parser import ResumeParser
from src.search_engine import IntelligentSearchEngine

def main():
    print("=" * 70)
    print("SARAH'S AI RESUME PARSER & SEARCH SYSTEM")
    print("=" * 70)

    resumes_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "data/resumes"))
    parser = ResumeParser()
    
    print(f"\n1. Ingesting and Parsing PDF Resumes from: {resumes_dir} ...")
    candidates = []
    
    for filename in sorted(os.listdir(resumes_dir)):
        if filename.endswith(".pdf"):
            fpath = os.path.join(resumes_dir, filename)
            parsed = parser.parse(fpath, filename=filename)
            candidates.append(parsed)
            print(f"   [OK] Parsed: {parsed['name']} ({parsed['title']}) - {parsed['experience_years']} yrs exp, {parsed['highest_degree']}")

    print(f"\nSuccessfully indexed {len(candidates)} candidates.")

    # Initialize search engine
    search_engine = IntelligentSearchEngine(candidates)

    # Demo queries
    demo_queries = [
        "Python developers with 3+ years experience",
        "DevOps engineer with AWS and Kubernetes",
        "Data Scientist with PhD and PyTorch",
        "Frontend React developer"
    ]

    print("\n" + "=" * 70)
    print("2. RUNNING DEMO SEARCH QUERIES & SUITABILITY RANKING")
    print("=" * 70)

    for q in demo_queries:
        print(f"\nQUERY: \"{q}\"")
        print("-" * 70)
        results = search_engine.search(query=q)
        
        for rank, res in enumerate(results[:3], 1):
            cand = res["candidate"]
            score = res["suitability_score"]
            match_det = res["match_details"]
            print(f"   Rank #{rank} | {cand['name']} - {score}% Match")
            print(f"            Title      : {cand['title']}")
            print(f"            Experience : {cand['experience_years']} Years (Match: {match_det['exp_match']})")
            print(f"            Degree     : {cand['highest_degree']}")
            print(f"            Skills     : {', '.join(cand['skills'][:8])}")
            print(f"            Contact    : {cand['contact']['email']} | {cand['contact']['phone']}")
            print()

if __name__ == '__main__':
    main()
