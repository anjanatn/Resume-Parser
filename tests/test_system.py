import unittest
import os
import sys

# Ensure src is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.parser import ResumeParser
from src.search_engine import IntelligentSearchEngine
from src.generator import generate_all_sample_resumes

class TestResumeParserSystem(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.resumes_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../data/resumes'))
        os.makedirs(cls.resumes_dir, exist_ok=True)
        generate_all_sample_resumes(cls.resumes_dir)
        
        cls.parser = ResumeParser()
        cls.parsed_candidates = []
        
        for fname in sorted(os.listdir(cls.resumes_dir)):
            if fname.endswith('.pdf'):
                fpath = os.path.join(cls.resumes_dir, fname)
                parsed = cls.parser.parse(fpath, filename=fname)
                cls.parsed_candidates.append(parsed)

    def test_parsed_count(self):
        self.assertEqual(len(self.parsed_candidates), 10, "Should parse all 10 sample resumes.")

    def test_extraction_fields(self):
        for candidate in self.parsed_candidates:
            self.assertIsNotNone(candidate["name"])
            self.assertTrue(len(candidate["name"]) > 0)
            self.assertIn("@", candidate["contact"]["email"])
            self.assertTrue(len(candidate["skills"]) > 0, f"Skills should be extracted for {candidate['name']}")
            self.assertGreaterEqual(candidate["experience_years"], 1.0)
            self.assertIn(candidate["highest_degree"], ["Bachelor's", "Master's", "PhD"])

    def test_python_3plus_years_search(self):
        search_engine = IntelligentSearchEngine(self.parsed_candidates)
        query = "Python developers with 3+ years experience"
        results = search_engine.search(query=query)
        
        self.assertGreater(len(results), 0)
        top_candidate = results[0]["candidate"]
        top_score = results[0]["suitability_score"]
        
        # Verify Alex Chen or Maria Garcia or Marcus Johnson rank at top for Python 3+ years
        self.assertIn("Python", top_candidate["skills"])
        self.assertGreaterEqual(top_candidate["experience_years"], 3.0)
        self.assertGreaterEqual(top_score, 80.0, "Top candidates should have >80% suitability score.")

    def test_devops_search(self):
        search_engine = IntelligentSearchEngine(self.parsed_candidates)
        query = "DevOps engineer AWS Kubernetes Terraform"
        results = search_engine.search(query=query)
        
        top_candidate = results[0]["candidate"]
        self.assertIn("Priya Sharma", top_candidate["name"])
        self.assertIn("AWS", top_candidate["skills"])
        self.assertIn("Kubernetes", top_candidate["skills"])

    def test_phd_data_science_search(self):
        search_engine = IntelligentSearchEngine(self.parsed_candidates)
        query = "Data scientist PyTorch NLP PhD"
        results = search_engine.search(query=query)
        
        top_candidate = results[0]["candidate"]
        self.assertIn("Marcus Johnson", top_candidate["name"])
        self.assertEqual(top_candidate["highest_degree"], "PhD")

    def test_jd_matcher_and_skill_gaps(self):
        search_engine = IntelligentSearchEngine(self.parsed_candidates)
        jd_text = "We need a Senior Python Engineer with 3+ years experience in FastAPI, Docker, and AWS."
        match_data = search_engine.match_job_description(jd_text)
        
        self.assertIn("skills", match_data["jd_requirements"])
        self.assertIn("Python", match_data["jd_requirements"]["skills"])
        self.assertGreater(len(match_data["results"]), 0)
        
        top_res = match_data["results"][0]
        self.assertIn("outreach_draft", top_res)
        self.assertIn("matched_skills", top_res["match_details"])
        self.assertIn("missing_skills", top_res["match_details"])

    def test_anonymous_id_generation(self):
        for candidate in self.parsed_candidates:
            self.assertIn("anonymous_id", candidate)
            self.assertTrue(candidate["anonymous_id"].startswith("CAND-"))

if __name__ == '__main__':
    unittest.main()
