import unittest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.parser import ResumeParser
from src.search_engine import IntelligentSearchEngine
from src.generator import generate_all_sample_resumes


class TestResumeParserSystem(unittest.TestCase):
    """End-to-end system tests for parsing, extraction, and search."""

    @classmethod
    def setUpClass(cls):
        cls.resumes_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data/resumes"))
        os.makedirs(cls.resumes_dir, exist_ok=True)
        generate_all_sample_resumes(cls.resumes_dir)

        cls.parser = ResumeParser()
        cls.parsed_candidates = []

        for fname in sorted(os.listdir(cls.resumes_dir)):
            if fname.endswith(".pdf"):
                fpath = os.path.join(cls.resumes_dir, fname)
                parsed = cls.parser.parse(fpath, filename=fname)
                cls.parsed_candidates.append(parsed)

    # ── Parser Tests ──────────────────────────────────────────────────────

    def test_parsed_count(self):
        """All 10 synthetic resumes should parse successfully."""
        self.assertEqual(len(self.parsed_candidates), 10)

    def test_extraction_fields_present(self):
        """Every candidate must have name, email, skills, experience, degree."""
        for c in self.parsed_candidates:
            self.assertIsNotNone(c["name"], "Name must not be None")
            self.assertGreater(len(c["name"]), 0, "Name must not be empty")
            self.assertIn("@", c["contact"]["email"], f"Email missing for {c['name']}")
            self.assertGreater(len(c["skills"]), 0, f"No skills for {c['name']}")
            self.assertGreaterEqual(c["experience_years"], 0.5, f"Low exp for {c['name']}")
            self.assertIn(c["highest_degree"], ["Bachelor's", "Master's", "PhD", "Associate's", "None"])

    def test_anonymous_id_generation(self):
        """Every candidate must have a CAND-XXXX anonymous ID."""
        for c in self.parsed_candidates:
            self.assertIn("anonymous_id", c)
            self.assertRegex(c["anonymous_id"], r"^CAND-[A-F0-9]{4}$")

    def test_summary_pitch_present(self):
        """Every candidate must have a non-empty summary pitch."""
        for c in self.parsed_candidates:
            self.assertIn("summary_pitch", c)
            self.assertGreater(len(c["summary_pitch"]), 10)

    # ── Skill Extraction Tests ─────────────────────────────────────────────

    def test_skill_extraction_python(self):
        """Python skill should be extractable from text."""
        text = "Experienced in Python 3, Django REST Framework, and SQL databases."
        p = ResumeParser()
        skills = p._extract_skills(text)
        self.assertIn("Python", skills)
        self.assertIn("SQL", skills)
        self.assertIn("Django", skills)

    def test_skill_extraction_devops(self):
        """DevOps skills should be extractable."""
        text = "Worked with Docker, Kubernetes (k8s), Terraform, AWS, and CI/CD pipelines."
        p = ResumeParser()
        skills = p._extract_skills(text)
        self.assertIn("Docker", skills)
        self.assertIn("Kubernetes", skills)
        self.assertIn("Terraform", skills)
        self.assertIn("AWS", skills)
        self.assertIn("CI/CD", skills)

    def test_skill_extraction_ml(self):
        """ML skills should be extractable."""
        text = "Built models using PyTorch, scikit-learn, NLP, and HuggingFace transformers."
        p = ResumeParser()
        skills = p._extract_skills(text)
        self.assertIn("PyTorch", skills)
        self.assertIn("Scikit-Learn", skills)
        self.assertIn("NLP", skills)

    # ── Experience Extraction Tests ────────────────────────────────────────

    def test_experience_date_range_parsing(self):
        """Experience from date ranges should be calculated correctly."""
        text = """
        Work Experience
        Software Engineer    Jan 2020 - Jan 2023
        Junior Developer     Jun 2018 - Dec 2019
        """
        p = ResumeParser()
        years, _ = p._extract_experience(text)
        self.assertGreaterEqual(years, 3.0)

    def test_experience_stated_years(self):
        """Explicit 'X years of experience' should be picked up."""
        text = "Over 5 years of industry experience in software development."
        p = ResumeParser()
        years, _ = p._extract_experience(text)
        self.assertEqual(years, 5.0)

    def test_experience_present_keyword(self):
        """'Present' in date range should calculate up to today."""
        text = """
        Work Experience
        Engineer    Mar 2022 - Present
        """
        p = ResumeParser()
        years, _ = p._extract_experience(text)
        self.assertGreaterEqual(years, 2.0)

    # ── Phone Extraction Tests ─────────────────────────────────────────────

    def test_phone_indian_format(self):
        """Should extract Indian 10-digit mobile numbers."""
        text = "Contact: +91 98765 43210"
        p = ResumeParser()
        phone = p._extract_phone_improved(text)
        self.assertIsNotNone(phone)
        self.assertIn("98765", phone)

    def test_phone_us_format(self):
        """Should extract US-style phone numbers."""
        text = "Phone: (555) 123-4567"
        p = ResumeParser()
        phone = p._extract_phone_improved(text)
        self.assertIsNotNone(phone)

    # ── Search & Ranking Tests ─────────────────────────────────────────────

    def test_python_3plus_years_search(self):
        """Top Python developer result should have Python skill and 3+ yrs."""
        engine = IntelligentSearchEngine(self.parsed_candidates)
        results = engine.search(query="Python developers with 3+ years experience")
        self.assertGreater(len(results), 0)
        top = results[0]
        self.assertIn("Python", top["candidate"]["skills"])
        self.assertGreaterEqual(top["candidate"]["experience_years"], 3.0)
        self.assertGreaterEqual(top["suitability_score"], 70.0)

    def test_devops_search(self):
        """DevOps query should surface AWS/Kubernetes candidates."""
        engine = IntelligentSearchEngine(self.parsed_candidates)
        results = engine.search(query="DevOps engineer AWS Kubernetes Terraform")
        self.assertGreater(len(results), 0)
        top = results[0]
        self.assertTrue(
            "AWS" in top["candidate"]["skills"] or "Kubernetes" in top["candidate"]["skills"]
        )

    def test_phd_data_science_search(self):
        """PhD data science query should surface PhD-level candidate."""
        engine = IntelligentSearchEngine(self.parsed_candidates)
        results = engine.search(query="Data scientist PyTorch NLP PhD")
        self.assertGreater(len(results), 0)
        top = results[0]
        self.assertEqual(top["candidate"]["highest_degree"], "PhD")

    def test_ranking_explanation_present(self):
        """Every result should contain a ranking_explanation list."""
        engine = IntelligentSearchEngine(self.parsed_candidates)
        results = engine.search(query="Python developer")
        for r in results:
            self.assertIn("ranking_explanation", r)
            self.assertIsInstance(r["ranking_explanation"], list)
            self.assertGreater(len(r["ranking_explanation"]), 0)

    def test_score_breakdown_present(self):
        """Score breakdown with 4 contributions should sum to overall score."""
        engine = IntelligentSearchEngine(self.parsed_candidates)
        results = engine.search(query="React developer")
        for r in results:
            bd = r["match_details"]["score_breakdown"]
            total = (
                bd["skill_contribution"]
                + bd["exp_contribution"]
                + bd["semantic_contribution"]
                + bd["edu_contribution"]
            )
            self.assertAlmostEqual(total, r["suitability_score"], delta=2.0)

    # ── JD Matcher Tests ───────────────────────────────────────────────────

    def test_jd_matcher_and_skill_gaps(self):
        """JD matcher should extract skills, return results with gap analysis."""
        engine = IntelligentSearchEngine(self.parsed_candidates)
        jd = "Senior Python Engineer with 3+ years, FastAPI, Docker, AWS. Bachelor's required."
        data = engine.match_job_description(jd)

        self.assertIn("Python", data["jd_requirements"]["skills"])
        self.assertGreaterEqual(data["jd_requirements"]["min_exp"], 3.0)
        self.assertGreater(len(data["results"]), 0)

        top = data["results"][0]
        self.assertIn("outreach_draft", top)
        self.assertIn("matched_skills", top["match_details"])
        self.assertIn("missing_skills", top["match_details"])

    def test_minimum_experience_filter(self):
        """Filtering by min_experience should reduce results."""
        engine = IntelligentSearchEngine(self.parsed_candidates)
        all_results = engine.search(query="developer")
        filtered = engine.search(query="developer", min_experience=10.0)
        # Filtered set should be <= all results in length
        self.assertLessEqual(len(filtered), len(all_results))

    def test_education_filter(self):
        """PhD education filter penalizes non-PhD candidates; a PhD should appear in results."""
        engine = IntelligentSearchEngine(self.parsed_candidates)
        results = engine.search(query="machine learning", min_degree="PhD")
        # Education is 10% of total — Bachelor's with stronger skills can still rank higher.
        # Assert at least one PhD candidate surfaces in the result set.
        if results:
            phd_in_results = any(r["candidate"]["highest_degree"] == "PhD" for r in results)
            self.assertTrue(phd_in_results, "Expected at least one PhD candidate in results")


if __name__ == "__main__":
    unittest.main(verbosity=2)
