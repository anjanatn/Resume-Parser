import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from .utils import SKILLS_TAXONOMY, DEGREE_PATTERNS

class IntelligentSearchEngine:
    def __init__(self, candidates=None):
        self.candidates = candidates or []
        self.vectorizer = TfidfVectorizer(stop_words='english')
        self._update_index()

    def set_candidates(self, candidates):
        self.candidates = candidates
        self._update_index()

    def _update_index(self):
        if not self.candidates:
            self.tfidf_matrix = None
            return
        
        # Build TF-IDF document corpus from raw text + skills
        corpus = []
        for c in self.candidates:
            doc_text = f"{c['name']} {c['title']} {' '.join(c['skills'])} {c['raw_text']}"
            corpus.append(doc_text)
        
        try:
            self.tfidf_matrix = self.vectorizer.fit_transform(corpus)
        except Exception:
            self.tfidf_matrix = None

    def parse_natural_query(self, query):
        """Parse natural language query to extract structured criteria."""
        query_lower = query.lower()
        
        # 1. Extract requested skills
        req_skills = []
        for keyword, canonical in SKILLS_TAXONOMY.items():
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if keyword in ['c++', 'c#', '.net']:
                pattern = re.escape(keyword)
            if re.search(pattern, query_lower):
                if canonical not in req_skills:
                    req_skills.append(canonical)

        # 2. Extract experience constraint (e.g. "3+ years", "at least 5 yrs", "3-5 years")
        min_exp = 0.0
        exp_match = re.search(r'(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)', query_lower)
        if exp_match:
            try:
                min_exp = float(exp_match.group(1))
            except ValueError:
                min_exp = 0.0

        # 3. Extract degree requirement
        req_degree = None
        for pattern, degree_name, level in DEGREE_PATTERNS:
            if re.search(pattern, query_lower):
                req_degree = degree_name
                break

        return {
            "query_text": query,
            "skills": req_skills,
            "min_exp": min_exp,
            "min_degree": req_degree
        }

    def search(self, query="", filter_skills=None, min_experience=0.0, min_degree="Any"):
        """
        Executes hybrid search & suitability ranking.
        Returns candidates ranked by suitability percentage (0-100%).
        """
        if not self.candidates:
            return []

        # Parse query for natural intent
        parsed_query = self.parse_natural_query(query) if query else {"skills": [], "min_exp": 0.0, "min_degree": None}
        
        # Combine explicit filter skills with query skills
        target_skills = set(filter_skills or [])
        target_skills.update(parsed_query["skills"])
        target_skills = list(target_skills)
        
        target_min_exp = max(min_experience, parsed_query["min_exp"])
        
        degree_hierarchy = {"PhD": 5, "Master's": 4, "Bachelor's": 3, "Associate's": 2, "None": 0, "Any": 0}
        target_degree_level = degree_hierarchy.get(parsed_query["min_degree"] or min_degree, 0)

        # Calculate TF-IDF similarities
        tfidf_scores = [0.0] * len(self.candidates)
        if query and self.tfidf_matrix is not None:
            try:
                query_vec = self.vectorizer.transform([query])
                similarities = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
                tfidf_scores = similarities
            except Exception:
                pass

        results = []
        for idx, candidate in enumerate(self.candidates):
            candidate_skills = set(candidate.get("skills", []))
            
            # --- 1. Skill Match Score (40%) ---
            if target_skills:
                matched_skills = [s for s in target_skills if s in candidate_skills]
                skill_score = len(matched_skills) / len(target_skills)
            else:
                matched_skills = list(candidate_skills)
                skill_score = 1.0 if candidate_skills else 0.5

            # --- 2. Experience Match Score (30%) ---
            cand_exp = candidate.get("experience_years", 0.0)
            if target_min_exp > 0:
                if cand_exp >= target_min_exp:
                    exp_score = 1.0
                else:
                    # Gradual penalty for lower experience
                    exp_score = max(0.0, cand_exp / target_min_exp)
            else:
                exp_score = min(1.0, cand_exp / 5.0)  # Normalize 5+ years to 1.0

            # --- 3. Text / Role Semantic Relevance (20%) ---
            semantic_score = float(tfidf_scores[idx]) if query else 0.8

            # --- 4. Education Score (10%) ---
            cand_degree_level = degree_hierarchy.get(candidate.get("highest_degree", "None"), 0)
            if target_degree_level > 0:
                edu_score = 1.0 if cand_degree_level >= target_degree_level else max(0.5, cand_degree_level / target_degree_level)
            else:
                edu_score = 1.0 if cand_degree_level >= 3 else 0.7

            # Overall Weighted Suitability Score
            overall_score = (skill_score * 0.40) + (exp_score * 0.30) + (semantic_score * 0.20) + (edu_score * 0.10)
            overall_pct = round(overall_score * 100, 1)

            # Build breakdown explanation
            missing_skills = [s for s in target_skills if s not in candidate_skills] if target_skills else []
            
            # Build personalized outreach email draft
            outreach_draft = self.generate_outreach_email(
                candidate=candidate,
                role_or_query=query or "Software Engineering Role",
                matched_skills=matched_skills
            )

            results.append({
                "candidate": candidate,
                "suitability_score": overall_pct,
                "outreach_draft": outreach_draft,
                "match_details": {
                    "matched_skills": matched_skills,
                    "missing_skills": missing_skills,
                    "exp_match": f"{cand_exp} yrs (Req: {target_min_exp} yrs)" if target_min_exp > 0 else f"{cand_exp} yrs",
                    "edu_match": candidate.get("highest_degree", "None"),
                    "semantic_score_pct": round(semantic_score * 100, 1),
                    "skill_score_pct": round(skill_score * 100, 1),
                    "exp_score_pct": round(exp_score * 100, 1)
                }
            })

        # Sort candidates descending by suitability score
        results.sort(key=lambda x: x["suitability_score"], reverse=True)
        return results

    def match_job_description(self, jd_text):
        """
        Extracts requirements from full Job Description and ranks all candidates with skill gap analysis.
        """
        if not jd_text or not self.candidates:
            return {
                "jd_requirements": {"skills": [], "min_exp": 0.0, "min_degree": "Any"},
                "results": []
            }

        parsed_jd = self.parse_natural_query(jd_text)
        req_skills = parsed_jd["skills"]
        min_exp = parsed_jd["min_exp"]
        min_degree = parsed_jd["min_degree"] or "Any"

        # Search candidates using extracted JD parameters + full semantic text
        search_results = self.search(
            query=jd_text,
            filter_skills=req_skills,
            min_experience=min_exp,
            min_degree=min_degree
        )

        return {
            "jd_requirements": {
                "skills": req_skills,
                "min_exp": min_exp,
                "min_degree": min_degree
            },
            "results": search_results
        }

    def generate_outreach_email(self, candidate, role_or_query="Software Engineering Role", matched_skills=None):
        """Generates a personalized recruiter outreach email."""
        name = candidate.get("name", "Candidate")
        first_name = name.split()[0] if name else "there"
        exp = candidate.get("experience_years", 0)
        skills = matched_skills or candidate.get("skills", [])[:4]
        skills_str = ", ".join(skills[:3]) if skills else "your technical background"

        clean_role = role_or_query[:45].strip()

        return f"""Subject: Exciting Opportunity at our Startup - {clean_role}

Hi {first_name},

I came across your profile and was really impressed by your background as a {candidate.get('title', 'Engineer')} with {exp} years of industry experience, particularly your expertise in {skills_str}.

We are expanding our engineering team and are looking for someone with your specific strengths to help build our core products.

Would you be open to a quick 15-minute introductory conversation this week to discuss what we are building and see if it could be a great fit?

Looking forward to connecting!

Best regards,
Sarah & Recruiting Team"""

