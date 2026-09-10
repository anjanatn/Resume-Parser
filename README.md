# Resume Intelligence Platform

AI-powered resume processing and search system that transforms raw PDF/DOCX resumes into structured, searchable profiles — with natural language search, job description matching, and blind screening support.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         BROWSER (SPA)                           │
│   Dark-nav header  │  JD Matcher  │  Candidate Cards  │ Modals  │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP (JSON)
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Flask API  (api/index.py)                   │
│  GET /            POST /api/search    POST /api/match_jd        │
│  POST /api/upload POST /api/upload_url POST /api/update_status  │
└──────┬──────────────────────┬──────────────────────────────────┘
       │                      │
       ▼                      ▼
┌──────────────┐   ┌──────────────────────────────────────────────┐
│  ResumeParser│   │        IntelligentSearchEngine               │
│  src/parser.py   │        src/search_engine.py                  │
│              │   │                                              │
│ 1. PyMuPDF   │   │  Hybrid Scoring (100 pts):                   │
│ 2. pypdf     │   │    Skill Match       40%  (taxonomy lookup)  │
│ 3. OCR *     │   │    Experience Match  30%  (date ranges)      │
│ 4. DOCX      │   │    TF-IDF Semantic   20%  (bigram cosine)    │
│ 5. TXT       │   │    Education Match   10%  (degree hierarchy) │
└──────┬───────┘   └──────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────┐
│  src/utils.py            │
│  SKILLS_TAXONOMY (140+)  │
│  DEGREE_PATTERNS         │
│  Contact regex helpers   │
└──────────────────────────┘
       │
       ▼
┌──────────────────────────┐
│  ResumeParserUnlocked/   │  ← Real resumes (gitignored)
│  data/resumes/           │  ← Synthetic resumes (ReportLab)
└──────────────────────────┘
```

> \* OCR: requires `pytesseract` + Tesseract binary for scanned/image PDFs.

---

## Features

| Feature | Description |
|---|---|
| **Multi-format parsing** | PDF (digital + OCR scanned), DOCX, TXT |
| **Natural Language Search** | "Python devs with 3+ years" → ranked results |
| **JD Auto-Matcher** | Paste full job posting → auto-extract skills/exp → rank all candidates |
| **Skill Gap Analysis** | Per-candidate matched vs. missing skills |
| **Ranking Explanation** | Plain-English bullets explaining *why* each candidate ranked |
| **Blind Screening Mode** | Hide PII (name/email/phone/location), show anonymous IDs |
| **Side-by-Side Comparison** | Compare up to 3 candidates across all attributes |
| **Recruiter Pipeline** | Kanban-style status: New → Shortlisted → Interview Scheduled → Archived |
| **Outreach Email Generator** | Pre-drafted personalized recruiter email per candidate |
| **URL Resume Upload** | Paste Google Drive / Dropbox / direct PDF link |
| **CSV / JSON Export** | Download full candidate roster |
| **Evaluation Suite** | Precision@5, Recall@10, MRR, parsing accuracy |

---

## Quick Start

```bash
# Clone and install
git clone https://github.com/anjanatn/Resume-Parser.git
cd Resume-Parser
pip install -r requirements.txt

# Add your resumes to ResumeParserUnlocked/
# (or generate synthetic ones)
python src/generator.py

# Run the app
python api/index.py
# Open http://127.0.0.1:5000
```

---

## Installation

### Requirements

| Package | Purpose |
|---|---|
| `Flask>=3.0.0` | Web framework |
| `pymupdf>=1.23.0` | PDF text extraction |
| `pypdf>=3.17.0` | PDF fallback extractor |
| `scikit-learn>=1.3.0` | TF-IDF vectorizer & cosine similarity |
| `python-docx>=1.1.0` | DOCX support |
| `reportlab>=4.0.0` | Synthetic resume generation |
| `requests>=2.31.0` | URL resume fetching |

### Optional: OCR for Scanned PDFs

```bash
# Install Python packages
pip install pytesseract Pillow

# Install Tesseract binary (Windows)
# Download from: https://github.com/UB-Mannheim/tesseract/wiki
# Add to PATH after install
```

---

## API Reference

### `GET /`
Returns the main SPA.

### `POST /api/search`
Natural language candidate search.

**Request:**
```json
{
  "query": "Python developer with 3+ years",
  "min_exp": 3.0,
  "min_degree": "Bachelor's"
}
```

**Response:**
```json
{
  "success": true,
  "count": 8,
  "results": [
    {
      "candidate": { "name": "...", "skills": [...], ... },
      "suitability_score": 87.5,
      "ranking_explanation": [
        "Matches 4/4 required skills: Python, Django, AWS, Docker.",
        "5.0 yrs experience meets the 3.0 yr requirement.",
        "Bachelor's degree meets the Bachelor's requirement.",
        "Resume text is highly relevant to the search query."
      ],
      "match_details": {
        "matched_skills": ["Python", "Django"],
        "missing_skills": ["Kubernetes"],
        "skill_score_pct": 80.0,
        "exp_score_pct": 100.0,
        "edu_score_pct": 100.0,
        "semantic_score_pct": 72.3,
        "score_breakdown": {
          "skill_contribution": 32.0,
          "exp_contribution": 30.0,
          "semantic_contribution": 14.5,
          "edu_contribution": 10.0
        }
      },
      "outreach_draft": "Subject: ..."
    }
  ]
}
```

### `POST /api/match_jd`
Match candidates against a full Job Description.

**Request:**
```json
{ "jd_text": "We are looking for a Senior Python Engineer with 3+ years..." }
```

**Response:** Same as `/api/search` + `jd_requirements` object.

### `POST /api/upload`
Upload a resume file (PDF / DOCX / TXT).

**Request:** `multipart/form-data` with `file` field.

### `POST /api/upload_url`
Fetch and index a resume from a URL.

**Request:**
```json
{ "url": "https://drive.google.com/file/d/..." }
```

### `POST /api/update_status`
Update pipeline stage for a candidate.

**Request:**
```json
{ "id": "candidate_id", "status": "Shortlisted" }
```

---

## Ranking Algorithm

The suitability score (0–100%) is a **weighted composite**:

| Component | Weight | Signal |
|---|---|---|
| **Skill Match** | 40% | Fraction of target skills found in resume |
| **Experience Match** | 30% | Candidate years vs. required years |
| **Semantic Relevance** | 20% | TF-IDF cosine similarity (bigrams) |
| **Education Match** | 10% | Degree hierarchy vs. requirement |

Every result includes a `ranking_explanation` — plain-English bullets like:
- *"Matches 3/4 required skills: Python, Docker, AWS. Missing: Kubernetes."*
- *"5.0 yrs experience meets the 3.0 yr requirement."*
- *"Master's degree exceeds the Bachelor's requirement."*

---

## Sample Search Queries

| Query | Expected Top Result |
|---|---|
| `Python developers with 3+ years experience` | Python engineer with 3+ yrs |
| `DevOps engineer AWS Kubernetes Terraform` | Cloud/DevOps specialist |
| `Data Scientist PyTorch NLP PhD` | PhD ML researcher |
| `Full-Stack Python React Developer` | Full-stack engineer |
| `Senior Backend Engineer FastAPI Docker` | Backend engineer with API exp |

---

## Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run evaluation (Precision@5, Recall@10, MRR)
python evaluation/evaluation.py
```

### Test Coverage

| Test | Description |
|---|---|
| `test_parsed_count` | All 10 resumes parse without error |
| `test_extraction_fields_present` | Name, email, skills, degree, exp extracted |
| `test_anonymous_id_generation` | CAND-XXXX IDs are deterministic |
| `test_summary_pitch_present` | Auto-generated recruiter pitch exists |
| `test_skill_extraction_python` | Python/SQL/Django detected from text |
| `test_skill_extraction_devops` | Docker/K8s/Terraform detected |
| `test_skill_extraction_ml` | PyTorch/Scikit-Learn/NLP detected |
| `test_experience_date_range_parsing` | Date ranges summed correctly |
| `test_experience_stated_years` | "5 years of experience" → 5.0 |
| `test_experience_present_keyword` | "Present" → current date |
| `test_phone_indian_format` | +91 10-digit numbers extracted |
| `test_phone_us_format` | (555) 123-4567 extracted |
| `test_python_3plus_years_search` | Python 3+ yr query → Python dev at top |
| `test_devops_search` | DevOps query → AWS/K8s candidate at top |
| `test_phd_data_science_search` | PhD query → PhD candidate at top |
| `test_ranking_explanation_present` | Explanation bullets in every result |
| `test_score_breakdown_present` | 4 contributions sum to overall score |
| `test_jd_matcher_and_skill_gaps` | JD extracts skills + returns gap analysis |
| `test_minimum_experience_filter` | 10yr filter reduces result set |
| `test_education_filter` | PhD filter puts PhD candidate at top |

---

## Evaluation Metrics

Run `python evaluation/evaluation.py` to get:

- **Precision@5** — what fraction of top-5 results are relevant?
- **Recall@10** — what fraction of all relevant candidates appear in top-10?
- **MRR** — Mean Reciprocal Rank (1/rank of first relevant result)
- **Parsing Accuracy** — % of resumes with email, phone, skills, degree, exp extracted

---

## AI Technologies Used

### 1. TF-IDF with Bigrams (`scikit-learn`)
Converts resume text into weighted term vectors. Bigram support captures phrases like "machine learning", "deep learning", "REST API" — improving semantic matching precision over single-token TF-IDF.

### 2. Cosine Similarity Ranking
Query and document vectors are compared using cosine distance in high-dimensional TF-IDF space. Candidates are ranked by how semantically close their full resume text is to the search query.

### 3. OCR Pipeline (pytesseract + PyMuPDF)
For scanned PDFs where digital text is unavailable: renders each page at 200 DPI using PyMuPDF, then applies Tesseract OCR. Enables parsing of physically-scanned resumes.

### 4. Multi-Signal Scoring
Rather than a single signal, the ranking uses a weighted combination of skill match, experience gap, semantic similarity, and degree hierarchy — making rankings more robust than keyword-only or TF-IDF-only approaches.

### 5. Future: Dense Embeddings (Sentence Transformers)
Replacing TF-IDF with models like `all-MiniLM-L6-v2` would capture semantic synonyms (e.g., "ML Engineer" ↔ "Machine Learning Engineer") without exact keyword match.

### 6. Future: LLM-based Extraction
GPT-4/Gemini structured output for extracting companies, roles, dates, and responsibilities with higher fidelity than regex — especially for creative or non-standard resume layouts.

### 7. Future: Vector Database
`ChromaDB` or `Pinecone` for ANN (approximate nearest neighbor) search over dense embeddings — enabling sub-millisecond search across millions of resumes.

---

## Project Structure

```
RESUME_PARSER/
├── api/
│   └── index.py              # Flask app & API endpoints
├── src/
│   ├── parser.py             # Resume parser (PDF/DOCX/TXT/OCR)
│   ├── search_engine.py      # Hybrid search & ranking engine
│   ├── utils.py              # Skills taxonomy, degree patterns, regex
│   └── generator.py          # Synthetic resume generator (ReportLab)
├── templates/
│   └── index.html            # Single-page app UI
├── evaluation/
│   └── evaluation.py         # Precision@5, Recall@10, MRR, parsing accuracy
├── tests/
│   └── test_system.py        # 20 unit & integration tests
├── data/
│   └── resumes/              # Synthetic PDF resumes
├── ResumeParserUnlocked/     # Real resumes (gitignored)
├── requirements.txt
└── README.md
```

---

## Limitations

| Limitation | Details |
|---|---|
| **Two-column PDFs** | PyMuPDF reads columns left-to-right linearly, mixing content. Needs layout analysis. |
| **Name extraction** | Relies on first-line heuristics; may fail for image-heavy or creatively-formatted resumes. |
| **OCR quality** | Tesseract accuracy drops for handwritten text, decorative fonts, or low-DPI scans. |
| **In-memory storage** | Pipeline status is lost on server restart (no database persistence). |
| **Skills taxonomy** | Fixed list of ~140 skills; niche or emerging skills may be missed. |
| **No deduplication** | Uploading the same resume twice creates two separate entries. |

---

## Future Improvements

- [ ] Dense embeddings with Sentence Transformers for semantic synonym matching
- [ ] LLM-based structured extraction (roles, responsibilities, companies)
- [ ] Vector database (ChromaDB) for scalable nearest-neighbor search
- [ ] Better two-column PDF layout analysis using bounding box clustering
- [ ] Persistent database (SQLite/PostgreSQL) for pipeline status and history
- [ ] Resume preview/download (serve original file)
- [ ] Multi-language support (French, Spanish, Hindi CVs)
- [ ] Resume scoring feedback loop (recruiter thumbs up/down to tune weights)

---

## License

MIT
