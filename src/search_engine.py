import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from .utils import SKILLS_TAXONOMY, DEGREE_PATTERNS


class IntelligentSearchEngine:
    """
    Hybrid Resume Search & Ranking Engine.

    Scoring breakdown (total = 100%):
      - Skill Match        40%  — fraction of target skills found in resume
      - Experience Match   30%  — years relative to requirement
      - Semantic Relevance 20%  — TF-IDF cosine similarity of full text vs query
      - Education Match    10%  — degree level relative to requirement

    Ranking explanation is returned per-candidate so the UI can display it.
    """

    DEGREE_HIERARCHY = {
        "PhD": 5, "Master's": 4, "Bachelor's": 3, "Associate's": 2, "None": 0, "Any": 0
    }

    def __init__(self, candidates=None, use_embeddings=True):
        self.candidates = candidates or []
        self.vectorizer = TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2),      # Captures bigrams like "machine learning"
            min_df=1,
            sublinear_tf=True        # Log-scale TF dampening for rare terms
        )
        self.encoder = None
        if use_embeddings:
            try:
                from sentence_transformers import SentenceTransformer
                self.encoder = SentenceTransformer("all-MiniLM-L6-v2")
            except Exception:
                self.encoder = None
        self._update_index()

    def set_candidates(self, candidates):
        self.candidates = candidates
        self._update_index()

    def _update_index(self):
        if not self.candidates:
            self.tfidf_matrix = None
            self.dense_embeddings = None
            return
        corpus = [
            f"{c['name']} {c['title']} {' '.join(c['skills'])} {c['raw_text']}"
            for c in self.candidates
        ]
        try:
            self.tfidf_matrix = self.vectorizer.fit_transform(corpus)
        except Exception:
            self.tfidf_matrix = None
            
        if self.encoder is not None:
            try:
                self.dense_embeddings = self.encoder.encode(corpus, convert_to_numpy=True)
            except Exception:
                self.dense_embeddings = None
        else:
            self.dense_embeddings = None

    # ───────────────────────── QUERY PARSING ────────────────────────────────

    def parse_natural_query(self, query):
        """Extract skills, experience, and degree requirements from free text."""
        q = query.lower()
        req_skills = []
        for keyword, canonical in SKILLS_TAXONOMY.items():
            pat = (
                re.escape(keyword)
                if keyword in ["c++", "c#", ".net"]
                else r"(?<![a-zA-Z])" + re.escape(keyword) + r"(?![a-zA-Z])"
            )
            if re.search(r"(?i)" + pat, q) and canonical not in req_skills:
                req_skills.append(canonical)

        min_exp = 0.0
        exp_m = re.search(r"(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)", q)
        if exp_m:
            try:
                min_exp = float(exp_m.group(1))
            except ValueError:
                pass

        req_degree = None
        for pattern, degree_name, _ in DEGREE_PATTERNS:
            if re.search(pattern, q):
                req_degree = degree_name
                break

        return {"query_text": query, "skills": req_skills, "min_exp": min_exp, "min_degree": req_degree}

    # ───────────────────────── MAIN SEARCH ──────────────────────────────────

    def search(self, query="", filter_skills=None, min_experience=0.0, min_degree="Any"):
        """
        Hybrid search with weighted suitability scoring.
        Returns candidates ranked highest → lowest with full ranking explanation.
        """
        if not self.candidates:
            return []

        parsed = self.parse_natural_query(query) if query else {"skills": [], "min_exp": 0.0, "min_degree": None}

        target_skills = list(set(filter_skills or []) | set(parsed["skills"]))
        target_min_exp = max(min_experience, parsed["min_exp"])
        target_degree_level = self.DEGREE_HIERARCHY.get(parsed["min_degree"] or min_degree, 0)

        # Semantic similarity scores (Dense embeddings + TF-IDF fallback)
        semantic_scores = [0.0] * len(self.candidates)
        if query:
            if self.encoder is not None and self.dense_embeddings is not None:
                try:
                    q_emb = self.encoder.encode([query], convert_to_numpy=True)
                    dense_sims = cosine_similarity(q_emb, self.dense_embeddings).flatten().tolist()
                    semantic_scores = [max(0.0, float(s)) for s in dense_sims]
                except Exception:
                    pass
            
            # If dense embeddings were not used or all 0, use TF-IDF
            if all(s == 0.0 for s in semantic_scores) and self.tfidf_matrix is not None:
                try:
                    q_vec = self.vectorizer.transform([query])
                    tfidf_scores = cosine_similarity(q_vec, self.tfidf_matrix).flatten().tolist()
                    semantic_scores = [max(0.0, float(s)) for s in tfidf_scores]
                except Exception:
                    pass

        results = []
        for idx, candidate in enumerate(self.candidates):
            cand_skills = set(candidate.get("skills", []))

            # ── 1. Skill Score (40%) ──────────────────────────────────────
            if target_skills:
                matched_skills = [s for s in target_skills if s in cand_skills]
                missing_skills = [s for s in target_skills if s not in cand_skills]
                skill_score = len(matched_skills) / len(target_skills)
            else:
                matched_skills = sorted(cand_skills)
                missing_skills = []
                skill_score = 1.0 if cand_skills else 0.5

            # ── 2. Experience Score (30%) ─────────────────────────────────
            cand_exp = candidate.get("experience_years", 0.0)
            if target_min_exp > 0:
                if cand_exp >= target_min_exp:
                    exp_score = min(1.0, 0.85 + 0.15 * min((cand_exp - target_min_exp) / target_min_exp, 1.0))
                else:
                    exp_score = max(0.0, cand_exp / target_min_exp)
            else:
                exp_score = min(1.0, cand_exp / 5.0)

            # ── 3. Semantic / TF-IDF Score (20%) ─────────────────────────
            semantic_score = float(tfidf_scores[idx]) if query else 0.8

            # ── 4. Education Score (10%) ──────────────────────────────────
            cand_deg_level = self.DEGREE_HIERARCHY.get(candidate.get("highest_degree", "None"), 0)
            if target_degree_level > 0:
                edu_score = 1.0 if cand_deg_level >= target_degree_level else max(0.4, cand_deg_level / target_degree_level)
            else:
                edu_score = 1.0 if cand_deg_level >= 3 else 0.7

            # ── Overall Weighted Score ─────────────────────────────────────
            overall = (skill_score * 0.40) + (exp_score * 0.30) + (semantic_score * 0.20) + (edu_score * 0.10)
            overall_pct = round(min(overall * 100, 100.0), 1)

            # ── Ranking Explanation ────────────────────────────────────────
            explanation = self._build_explanation(
                candidate=candidate,
                target_skills=target_skills,
                matched_skills=matched_skills,
                missing_skills=missing_skills,
                skill_score=skill_score,
                exp_score=exp_score,
                semantic_score=semantic_score,
                edu_score=edu_score,
                target_min_exp=target_min_exp,
                cand_exp=cand_exp,
                target_degree_level=target_degree_level,
                cand_deg_level=cand_deg_level,
            )

            outreach_draft = self.generate_outreach_email(
                candidate=candidate,
                role_or_query=query or "Software Engineering Role",
                matched_skills=matched_skills,
            )

            results.append({
                "candidate": candidate,
                "suitability_score": overall_pct,
                "outreach_draft": outreach_draft,
                "ranking_explanation": explanation,
                "match_details": {
                    "matched_skills": matched_skills,
                    "missing_skills": missing_skills,
                    "exp_match": (
                        f"{cand_exp} yrs (Required: {target_min_exp} yrs)"
                        if target_min_exp > 0
                        else f"{cand_exp} yrs"
                    ),
                    "edu_match": candidate.get("highest_degree", "None"),
                    "semantic_score_pct": round(semantic_score * 100, 1),
                    "skill_score_pct": round(skill_score * 100, 1),
                    "exp_score_pct": round(exp_score * 100, 1),
                    "edu_score_pct": round(edu_score * 100, 1),
                    # Weighted contributions for transparency
                    "score_breakdown": {
                        "skill_contribution": round(skill_score * 0.40 * 100, 1),
                        "exp_contribution": round(exp_score * 0.30 * 100, 1),
                        "semantic_contribution": round(semantic_score * 0.20 * 100, 1),
                        "edu_contribution": round(edu_score * 0.10 * 100, 1),
                    }
                },
            })

        results.sort(key=lambda x: x["suitability_score"], reverse=True)
        return results

    # ─────────────────────── RANKING EXPLANATION ────────────────────────────

    def _build_explanation(
        self, candidate, target_skills, matched_skills, missing_skills,
        skill_score, exp_score, semantic_score, edu_score,
        target_min_exp, cand_exp, target_degree_level, cand_deg_level,
    ):
        """
        Plain-English explanation of why this candidate ranked where they did.
        Returns a list of bullet strings.
        """
        bullets = []
        name_short = candidate.get("name", "This candidate").split()[0]

        # Skill explanation
        n_match = len(matched_skills)
        n_total = len(target_skills)
        if n_total > 0:
            if n_match == n_total:
                bullets.append(f"Matches all {n_total} required skill(s): {', '.join(matched_skills[:5])}.")
            elif n_match > 0:
                bullets.append(
                    f"Matches {n_match}/{n_total} required skills: {', '.join(matched_skills[:4])}."
                    + (f" Missing: {', '.join(missing_skills[:3])}." if missing_skills else "")
                )
            else:
                bullets.append(f"No required skills matched (has {len(candidate.get('skills', []))} unrelated skills).")
        else:
            bullets.append(f"Has {len(candidate.get('skills', []))} skills detected: {', '.join(candidate.get('skills', [])[:5])}.")

        # Experience explanation
        if target_min_exp > 0:
            if cand_exp >= target_min_exp:
                bullets.append(f"{cand_exp} yrs experience meets the {target_min_exp} yr requirement.")
            else:
                gap = round(target_min_exp - cand_exp, 1)
                bullets.append(f"{cand_exp} yrs experience is {gap} yrs below the {target_min_exp} yr requirement.")
        else:
            bullets.append(f"{cand_exp} yrs of total work experience.")

        # Education explanation
        degree_names = {5: "PhD", 4: "Master's", 3: "Bachelor's", 2: "Associate's", 0: "None"}
        cand_deg_name = candidate.get("highest_degree", "None")
        if target_degree_level > 0:
            req_name = degree_names.get(target_degree_level, "")
            if cand_deg_level >= target_degree_level:
                bullets.append(f"{cand_deg_name} degree meets the {req_name} requirement.")
            else:
                bullets.append(f"{cand_deg_name} degree is below the required {req_name} level.")
        else:
            bullets.append(f"Highest qualification: {cand_deg_name}.")

        # Semantic/relevance explanation
        if semantic_score >= 0.5:
            bullets.append("Resume text is highly relevant to the search query.")
        elif semantic_score >= 0.2:
            bullets.append("Resume text is moderately relevant to the search query.")
        else:
            bullets.append("Resume text has limited overlap with the search query.")

        return bullets

    # ─────────────────────── JD MATCHER ─────────────────────────────────────

    def match_job_description(self, jd_text):
        """
        Parse a full Job Description and rank all candidates with skill gap analysis.
        """
        if not jd_text or not self.candidates:
            return {"jd_requirements": {"skills": [], "min_exp": 0.0, "min_degree": "Any"}, "results": []}

        parsed = self.parse_natural_query(jd_text)
        req_skills = parsed["skills"]
        min_exp = parsed["min_exp"]
        min_degree = parsed["min_degree"] or "Any"

        results = self.search(
            query=jd_text,
            filter_skills=req_skills,
            min_experience=min_exp,
            min_degree=min_degree,
        )

        return {
            "jd_requirements": {"skills": req_skills, "min_exp": min_exp, "min_degree": min_degree},
            "results": results,
        }

    # ──────────────────── OUTREACH EMAIL ─────────────────────────────────────

    def generate_outreach_email(self, candidate, role_or_query="Software Engineering Role", matched_skills=None):
        """Generates a personalized recruiter outreach email."""
        name = candidate.get("name", "Candidate")
        first = name.split()[0] if name else "there"
        exp = candidate.get("experience_years", 0)
        skills = matched_skills or candidate.get("skills", [])[:4]
        skills_str = ", ".join(skills[:3]) if skills else "your technical expertise"
        clean_role = role_or_query[:50].strip()

        return (
            f"Subject: Exciting Opportunity - {clean_role}\n\n"
            f"Hi {first},\n\n"
            f"I came across your profile and was impressed by your background as a "
            f"{candidate.get('title', 'Engineer')} with {exp} years of experience, "
            f"particularly your expertise in {skills_str}.\n\n"
            f"We are expanding our engineering team and believe your skills are a great match "
            f"for what we are building.\n\n"
            f"Would you be open to a quick 15-minute conversation this week to explore if this "
            f"could be a great fit?\n\n"
            f"Looking forward to connecting!\n\n"
            f"Best regards,\n"
            f"Sarah & Recruiting Team"
        )
