# Resume Intelligence Platform

Enterprise AI-powered talent search, multi-format resume processing, Job Description (JD) matching, and recruitment analytics platform with n8n workflow automation support.

---

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Core Capabilities](#core-capabilities)
3. [Quick Start (Local Development)](#quick-start-local-development)
4. [Deployment to Vercel](#deployment-to-vercel)
5. [Automated Workflows with n8n](#automated-workflows-with-n8n)
6. [Database Configuration (SQLite & PostgreSQL)](#database-configuration-sqlite--postgresql)
7. [API Specification](#api-specification)
8. [Suitability Scoring & Ranking Algorithm](#suitability-scoring--ranking-algorithm)
9. [Evaluation Suite & Benchmarks](#evaluation-suite--benchmarks)
10. [Test Suite](#test-suite)
11. [Project Directory Structure](#project-directory-structure)
12. [License](#license)

---

## System Architecture

```
+---------------------------------------------------------------------------------+
|                              BROWSER CLIENT (SPA)                               |
|   Talent Dashboard  |  Candidate Search  |  JD Auto-Matcher  |  Candidate Dossier  |
+----------------------------------------+----------------------------------------+
                                         | HTTP / JSON REST
                                         v
+---------------------------------------------------------------------------------+
|                            FLASK API (api/index.py)                             |
|  GET  /                  GET  /api/dashboard_stats   POST /api/search           |
|  POST /api/upload        POST /api/upload_url        POST /api/match_jd        |
|  POST /api/update_status POST /api/webhook (n8n)     GET  /api/candidates      |
+──────────────+─────────────────────────+───────────────────────────+────────────+
               |                         |                           |
               v                         v                           v
+--------------------------+   +--------------------------+   +-------------------+
|       ResumeParser       |   | IntelligentSearchEngine  |   |     Notifier      |
|      (src/parser.py)     |   |  (src/search_engine.py)  |   | (src/notifier.py) |
|                          |   |                          |   |                   |
| 1. PyMuPDF               |   | * Skill Match (40%)      |   | * HR Email Alerts |
| 2. pypdf fallback        |   | * Seniority Match (30%)  |   |   (Score >= 80%)  |
| 3. OCR (Tesseract)       |   | * Semantic TF-IDF (20%)  |   | * n8n Webhook     |
| 4. DOCX & TXT Extraction |   | * Education Match (10%)  |   |   Event Dispatch  |
+──────────────+───────────+   +──────────────+───────────+   +───────────────────+
               |                              |
               +──────────────+───────────────+
                              |
                              v
+---------------------------------------------------------------------------------+
|                       PERSISTENCE LAYER (db/database.py)                        |
|  SQLite (db/resumes.db / /tmp/resumes.db) | PostgreSQL Ready                    |
|  * Candidates Table (Structured attributes, contact, SHA-256 content hash)      |
|  * Events Audit Log (Lifecycle transitions, ingestion logs, match triggers)     |
|  * Deduplication Engine (Content Hash & Normalized Email Lookup)                |
+---------------------------------------------------------------------------------+
```

---

## Core Capabilities

* **Interactive Talent Analytics Dashboard**: Real-time Chart.js visualizations for top skills distribution, recruitment pipeline funnel, seniority histograms, degree levels, and candidate audit stream.
* **Hybrid Intelligent Search**: Natural language query parsing (e.g. `Python developers with 3+ years experience and AWS`) with multi-factor scoring and human-readable ranking explanations.
* **Job Description Auto-Matcher**: Automated skill extraction from unstructured job postings, candidate suitability calculation, and skill gap identification.
* **Deduplication Engine**: Normalized SHA-256 content hashing and email matching to flag duplicate uploads without interrupting workflows.
* **Data Persistence**: SQLite database with auto-migration, complete candidate profile storage, and event logging.
* **n8n Workflow Automation**: Bi-directional integration via `POST /api/webhook` and outbound event dispatching for automated ATS pipelines.
* **Automated HR Alerts**: Automatic email dispatching via SMTP when candidate suitability reaches 80% or higher.
* **Blind Screening Mode**: DE&I compliance mode masking candidate names, emails, telephone numbers, and locations with deterministic `CAND-XXXX` identifiers.
* **5-Stage Recruiter Pipeline**: Lifecycle stage tracking across `New`, `Shortlisted`, `Interview`, `Hired`, and `Rejected`.
* **Multi-Format & OCR Parsing**: Digital PDFs, Microsoft Word (.docx), plain text (.txt), and scanned image-based PDFs using Tesseract OCR.
* **Side-by-Side Comparison**: Direct comparative analysis of up to 3 candidate dossiers simultaneously.
* **Data Export**: One-click download of candidate rosters in structured CSV or JSON formats.

---

## Quick Start (Local Development)

### Prerequisites
* Python 3.10, 3.11, or 3.12
* pip

### Installation

```bash
# 1. Clone repository
git clone https://github.com/anjanatn/Resume-Parser.git
cd Resume-Parser

# 2. Install dependencies
pip install -r requirements.txt

# 3. (Optional) Configure environment variables
cp .env.example .env

# 4. Launch the application
python api/index.py
```

Open **[http://127.0.0.1:5000](http://127.0.0.1:5000)** in your browser.

---

## Deployment to Vercel

The repository is pre-configured for Vercel Serverless Functions with `vercel.json` routing and serverless `/tmp` database initialization.

### Option A: Deploy via GitHub (Recommended)

1. Navigate to **[vercel.com/new](https://vercel.com/new)**.
2. Select your repository: **`anjanatn/Resume-Parser`**.
3. Keep default settings (`Framework Preset: Other`, Root Directory: `./`).
4. Click **Deploy**.

### Option B: Deploy via Vercel CLI

```powershell
# Authenticate and deploy
vercel

# Production deployment
vercel --prod
```

---

## Automated Workflows with n8n

The platform connects to [n8n](https://n8n.io/) to automate candidate ingestion from Gmail, Slack, Google Drive, or applicant portals.

### Inbound Ingestion Webhook (`POST /api/webhook`)

#### URL Mode:
```bash
curl -X POST http://127.0.0.1:5000/api/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://drive.google.com/file/d/example_resume/view",
    "target_jd": "Senior Python Engineer with Docker and AWS"
  }'
```

#### Base64 Document Mode:
```bash
curl -X POST http://127.0.0.1:5000/api/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "file_base64": "JVBERi0xLjQK...",
    "filename": "candidate_resume.pdf"
  }'
```

### Outbound Webhook Events
When `N8N_WEBHOOK_URL` is defined in `.env`, the system posts real-time events to your webhook:

| Event Type | Trigger | Payload Summary |
|---|---|---|
| `RESUME_INGESTED` | New resume parsed and indexed | Candidate ID, Name, Skills, Seniority |
| `HIGH_MATCH_FOUND` | Candidate scores >= 80% suitability | Candidate Name, Score, Target Role |
| `CANDIDATE_STATUS_CHANGED` | Pipeline stage transition | Candidate ID, New Status |

---

## Database Configuration (SQLite & PostgreSQL)

### SQLite (Default)
By default, the platform uses an embedded SQLite database stored at `db/resumes.db` (or `/tmp/resumes.db` on Vercel). No database setup or server management is required.

### PostgreSQL
To switch to PostgreSQL for enterprise production clusters:

1. Install psycopg2:
   ```bash
   pip install psycopg2-binary
   ```
2. Configure `.env`:
   ```env
   DATABASE_URL=postgresql://user:password@localhost:5432/resume_intelligence
   ```

---

## API Specification

### `GET /api/dashboard_stats`
Returns aggregated recruitment metrics, skill frequencies, and pipeline status distributions.

### `POST /api/search`
Queries candidate records with multi-factor weighting.

**Request Body:**
```json
{
  "query": "Python developers with 3+ years experience",
  "min_exp": 3.0,
  "min_degree": "Bachelor's"
}
```

**Response:**
```json
{
  "success": true,
  "count": 10,
  "results": [
    {
      "candidate": {
        "id": "alex_chen",
        "anonymous_id": "CAND-A1B2",
        "name": "Alex Chen",
        "title": "Senior Backend Engineer",
        "skills": ["Python", "FastAPI", "Docker", "AWS", "PostgreSQL"],
        "experience_years": 5.0,
        "highest_degree": "Bachelor's",
        "status": "Shortlisted"
      },
      "suitability_score": 92.5,
      "ranking_explanation": [
        "Matches all 4 required skills: Python, FastAPI, Docker, AWS.",
        "5.0 yrs experience meets the 3.0 yr requirement.",
        "Bachelor's degree meets the Bachelor's requirement.",
        "Resume text is highly relevant to the search query."
      ],
      "match_details": {
        "matched_skills": ["Python", "FastAPI", "Docker", "AWS"],
        "missing_skills": [],
        "skill_score_pct": 100.0,
        "exp_score_pct": 100.0,
        "semantic_score_pct": 82.5,
        "edu_score_pct": 100.0
      }
    }
  ]
}
```

### `POST /api/match_jd`
Evaluates all indexed resumes against raw Job Description text.

### `POST /api/upload`
Multipart upload for `.pdf`, `.docx`, or `.txt` files with duplicate detection.

### `POST /api/upload_url`
Fetches and indexes documents directly from cloud storage URLs (Google Drive, Dropbox, direct PDF links).

### `POST /api/update_status`
Updates candidate pipeline stage (`New`, `Shortlisted`, `Interview`, `Hired`, `Rejected`).

---

## Suitability Scoring & Ranking Algorithm

Candidate suitability (0–100%) is calculated using a composite four-factor evaluation formula:

$$\text{Suitability Score} = (0.40 \times \text{Skill}) + (0.30 \times \text{Seniority}) + (0.20 \times \text{Semantic Relevance}) + (0.10 \times \text{Education Level})$$

1. **Skill Match Score (40%)**: Fraction of required job skills matched against candidate's canonical skill profile.
2. **Seniority Score (30%)**: Verified candidate experience years evaluated against the target requirement threshold.
3. **Semantic Relevance (20%)**: Bigram TF-IDF cosine similarity capturing domain keywords and role descriptions.
4. **Education Level (10%)**: Educational qualification evaluated against the standard degree hierarchy (PhD > Master's > Bachelor's > Associate's).

---

## Evaluation Suite & Benchmarks

Run the evaluation script to compute information retrieval metrics across standard recruitment queries:

```bash
python evaluation/evaluation.py
```

### Metrics Output:
* **Precision@5**: Proportion of relevant candidates in top 5 results.
* **Recall@10**: Coverage of relevant candidates across the top 10 results.
* **Mean Reciprocal Rank (MRR)**: Reciprocal rank of the first relevant candidate.
* **Extraction Accuracy**: Attribute extraction completeness across contact info, skills, education, and work history.

---

## Test Suite

The system includes 24 automated unit and integration tests covering parser accuracy, regex extractors, database persistence, deduplication, search ranking, and notification dispatchers.

```bash
# Execute pytest suite
python -m pytest tests/test_system.py -v

# Execute standard unittest runner
python -m unittest tests.test_system -v
```

---

## Project Directory Structure

```
RESUME_PARSER/
├── api/
│   └── index.py              # Flask REST application & serverless handler
├── db/
│   ├── database.py           # SQLite / PostgreSQL persistence layer
│   └── resumes.db            # Default SQLite database
├── src/
│   ├── parser.py             # Multi-format document parser & OCR pipeline
│   ├── search_engine.py      # Hybrid semantic search & ranking engine
│   ├── notifier.py           # HR email alert & n8n webhook dispatcher
│   ├── utils.py              # Skills taxonomy, degree hierarchies, regex extractors
│   └── generator.py          # Synthetic resume benchmark generator
├── templates/
│   └── index.html            # Enterprise SPA dashboard & search interface
├── evaluation/
│   └── evaluation.py         # Precision@5, Recall@10, and MRR benchmark suite
├── tests/
│   └── test_system.py        # 24 automated test cases
├── data/
│   └── resumes/              # Reference resume files
├── requirements.txt          # Production dependencies
├── vercel.json               # Vercel serverless deployment specification
├── .env.example              # Environment variable configuration template
└── README.md                 # System documentation
```

---

## License

This project is licensed under the MIT License.
