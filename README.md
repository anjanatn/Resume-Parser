# Resume Intelligence Platform

AI-powered resume parsing, job description matching, candidate intelligence dashboard, and n8n workflow automation platform. Transforms raw PDF, DOCX, and TXT resumes into structured profiles with weighted suitability ranking, deduplication, and blind screening support.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           BROWSER CLIENT (SPA)                                  │
│  📊 Talent Dashboard  │  🔍 Candidate Search  │  💼 JD Matcher  │ 📑 Modals     │
└────────────────────────────────────────┬────────────────────────────────────────┘
                                         │ HTTP / JSON
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            FLASK API (api/index.py)                             │
│  GET /                   GET  /api/dashboard_stats    POST /api/search           │
│  POST /api/upload        POST /api/upload_url         POST /api/match_jd        │
│  POST /api/update_status POST /api/webhook (n8n)      GET  /api/candidates      │
└──────────────┬─────────────────────────┬───────────────────────────┬────────────┘
               │                         │                           │
               ▼                         ▼                           ▼
┌──────────────────────────┐   ┌──────────────────────────┐   ┌───────────────────┐
│       ResumeParser       │   │ IntelligentSearchEngine  │   │     Notifier      │
│      (src/parser.py)     │   │  (src/search_engine.py)  │   │ (src/notifier.py) │
│                          │   │                          │   │                   │
│ 1. PyMuPDF               │   │ • Skill Match (40%)      │   │ • HR Email Alerts │
│ 2. pypdf fallback        │   │ • Experience Match (30%) │   │   (Score >= 80%)  │
│ 3. OCR (pytesseract)     │   │ • Dense/TF-IDF (20%)     │   │ • n8n Webhook     │
│ 4. DOCX & TXT            │   │ • Education Match (10%)  │   │   Event Dispatch  │
└──────────────┬───────────┘   └──────────────┬───────────┘   └───────────────────┘
               │                              │
               └──────────────┬───────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                       PERSISTENCE LAYER (db/database.py)                        │
│  SQLite (db/resumes.db) / PostgreSQL Compatible                                 │
│  • Candidates Table (Skills, Exp, Education, Content SHA-256 Hash)              │
│  • Events Audit Log (Ingestion, Status Transitions, Matching Triggers)          │
│  • Duplicate Detection Engine (Content Hash & Email Matching)                   │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Key Features

| Capability | Description |
|---|---|
| 📊 **Interactive Dashboard** | Chart.js visualizations for Top Skills, Experience distribution, Pipeline funnel, Education qualifications, and recent talent activity |
| 🔍 **Hybrid Intelligent Search** | Natural language queries ("Python dev with 3+ yrs") with weighted suitability scores & plain-English ranking explanations |
| 💼 **JD Auto-Matcher** | Paste full job postings to auto-extract required skills, experience thresholds, and calculate candidate skill gaps |
| 🛡️ **Deduplication Engine** | SHA-256 content hashing and email matching to flag and manage duplicate resumes automatically |
| 🗄️ **Database Persistence** | SQLite database (`db/resumes.db`) storing full structured candidate profiles, work history, and audit events |
| ⚡ **n8n Automation & Webhooks** | `POST /api/webhook` to ingest resumes from email/Slack/Drive triggers, and outbound event dispatching |
| ✉️ **HR Email Alerts** | Automated notifications dispatched to HR when high-match candidates (score ≥ 80%) are evaluated |
| 🕶️ **Blind Screening Mode** | DE&I anonymization toggle hiding names, emails, phones, and locations with deterministic `CAND-XXXX` IDs |
| 🔄 **5-Stage Pipeline Tracking** | Recruiter pipeline lifecycle: `New` ➔ `Shortlisted` ➔ `Interview` ➔ `Hired` ➔ `Rejected` |
| 📄 **Multi-Format & OCR Parsing** | Digital PDFs, DOCX, TXT, and scanned image PDFs (via Tesseract OCR fallback) |
| ⚖️ **Side-by-Side Comparison** | Compare up to 3 candidates simultaneously across scores, skills, gaps, and degrees |
| 📥 **Recruiter Export** | One-click export to formatted CSV or JSON candidate rosters |

---

## Quick Start

```bash
# 1. Clone repository
git clone https://github.com/anjanatn/Resume-Parser.git
cd Resume-Parser

# 2. Install dependencies
pip install -r requirements.txt

# 3. (Optional) Configure environment
cp .env.example .env

# 4. Start the Application
python api/index.py
```

Visit **[http://127.0.0.1:5000](http://127.0.0.1:5000)** in your browser.

---

## Automation with n8n

The platform supports bi-directional integration with [n8n](https://n8n.io/) workflow automation:

### Inbound Webhook (`POST /api/webhook`)
Send resumes directly from Gmail, Slack, Google Drive, or ATS triggers to n8n, which posts to the platform:

```json
{
  "url": "https://drive.google.com/file/d/...",
  "target_jd": "Senior Python Backend Engineer with Docker and AWS"
}
```
*Or with base64 encoded document:*
```json
{
  "file_base64": "JVBERi0xLjQK...",
  "filename": "candidate_resume.pdf"
}
```

### Outbound Event Dispatch
Configure `N8N_WEBHOOK_URL` in `.env`. The system automatically notifies n8n on:
- `RESUME_INGESTED` — When a new candidate profile is created
- `HIGH_MATCH_FOUND` — When candidate suitability reaches ≥ 80%
- `CANDIDATE_STATUS_CHANGED` — When recruiter updates candidate stage

---

## Database Configuration (PostgreSQL / SQLite)

By default, the platform uses SQLite stored at `db/resumes.db` with zero configuration required.

### Switching to PostgreSQL:
1. Install psycopg2:
   ```bash
   pip install psycopg2-binary
   ```
2. Update `.env`:
   ```env
   DATABASE_URL=postgresql://user:password@localhost:5432/resume_intelligence
   ```

---

## API Reference

### `GET /api/dashboard_stats`
Returns aggregate statistics for dashboard visualizations.
```json
{
  "success": true,
  "data": {
    "total_candidates": 10,
    "shortlisted_count": 3,
    "hired_count": 1,
    "avg_experience": 4.8,
    "status_breakdown": { "New": 5, "Shortlisted": 3, "Interview": 1, "Hired": 1, "Rejected": 0 },
    "top_skills": { "Python": 8, "SQL": 6, "Docker": 5, "AWS": 4 },
    "experience_breakdown": { "0-2 Yrs (Entry)": 2, "2-5 Yrs (Mid)": 4, "5-8 Yrs (Senior)": 3, "8+ Yrs (Staff)": 1 }
  }
}
```

### `POST /api/search`
Query talent database using natural language or faceted criteria.
```json
{
  "query": "Python developer with 3+ years and cloud experience",
  "min_exp": 3.0,
  "min_degree": "Bachelor's"
}
```

### `POST /api/match_jd`
Matches resumes against raw job postings, returns skill gap analysis and ranking explanation.

### `POST /api/upload`
Multipart upload for `.pdf`, `.docx`, or `.txt`. Detects duplicates automatically.

### `POST /api/update_status`
Updates candidate status (`New`, `Shortlisted`, `Interview`, `Hired`, `Rejected`).

---

## Ranking Algorithm

Candidate suitability (0–100%) is computed via a transparent composite formula:

$$\text{Suitability Score} = (0.40 \times \text{Skill}) + (0.30 \times \text{Experience}) + (0.20 \times \text{Semantic}) + (0.10 \times \text{Education})$$

Each candidate result returns detailed, human-readable bullet points explaining the ranking factors and skill matches.

---

## Testing & Evaluation

Run the automated test suite (24 unit and integration tests):

```bash
# Run test suite
python -m pytest tests/test_system.py -v

# Run Precision@5, Recall@10, and Parsing Accuracy Evaluation
python evaluation/evaluation.py
```

---

## License

MIT License. Designed for rapid, automated talent screening and recruiter workflows.
