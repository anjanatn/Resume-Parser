# 📄 AI Resume Parser & Intelligent Candidate Search Engine

> An automated, AI-powered resume parsing and candidate ranking system built with Python, Flask, and Scikit-Learn — deployable on Vercel.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)
![Flask](https://img.shields.io/badge/Flask-3.0-black?logo=flask)
![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-1.3-orange?logo=scikit-learn)
![Vercel](https://img.shields.io/badge/Deployed%20on-Vercel-black?logo=vercel)
![License](https://img.shields.io/badge/License-MIT-green)

---

## ✨ Features

| Feature | Description |
|---|---|
| 📥 **PDF Parsing** | Extracts structured data from PDF resumes using PyMuPDF (with pypdf fallback) |
| 🧠 **Skills Extraction** | Matches 100+ skills against a canonical taxonomy (Python, AWS, React, Docker, etc.) |
| 📊 **Intelligent Ranking** | Hybrid TF-IDF + rule-based suitability scoring (skill, experience, education, semantic) |
| 🔍 **Natural Language Search** | Query in plain English: *"Senior Python developer with 5+ years and AWS experience"* |
| 🎯 **Faceted Filtering** | Filter by minimum experience (years), education level, and required skills |
| 📤 **Resume Upload** | Drag-and-drop upload for new PDF resumes with live re-indexing |
| 📋 **Contact Extraction** | Extracts email, phone, LinkedIn, GitHub, and location automatically |
| 🎓 **Education Detection** | Identifies PhD, Master's, Bachelor's, and Associate's degrees |
| 📅 **Experience Calculation** | Computes total years from date ranges in work history sections |
| 🌐 **Web UI** | Clean, responsive HTML/Tailwind CSS frontend + a Streamlit dashboard |

---

## 🏗️ Project Architecture

```
RESUME_PARSER/
│
├── api/
│   └── index.py              # Flask app — Vercel serverless entry point
│
├── src/
│   ├── parser.py             # Core PDF parsing & information extraction engine
│   ├── search_engine.py      # Hybrid TF-IDF + rule-based search & ranking engine
│   ├── generator.py          # Sample resume PDF generator (ReportLab)
│   └── utils.py              # Skills taxonomy, regex patterns, helper functions
│
├── templates/
│   └── index.html            # Responsive Tailwind CSS web interface
│
├── data/
│   └── resumes/              # 10 pre-generated sample PDF resumes
│
├── tests/
│   └── test_system.py        # Unit tests for parsing, search, and ranking
│
├── app.py                    # Streamlit interactive dashboard (local use)
├── demo.py                   # Quick CLI demo script
├── requirements.txt          # Python dependencies
├── vercel.json               # Vercel deployment configuration
└── README.md
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- pip

### 1. Clone the Repository

```bash
git clone https://github.com/anjanatn/Resume-Parser.git
cd Resume-Parser
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Generate Sample Resumes (Optional)

The `data/resumes/` directory already contains 10 pre-built sample PDF resumes. To regenerate them:

```bash
python src/generator.py
```

### 4. Run the Web App (Flask)

```bash
python api/index.py
```

Open [http://localhost:5000](http://localhost:5000) in your browser.

### 5. Run the Streamlit Dashboard (Alternative UI)

```bash
pip install streamlit pandas
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## 🌐 Deployment on Vercel

This project is configured for **Vercel Serverless** deployment.

### Deploy via Vercel CLI

```bash
npm install -g vercel
vercel --prod
```

### Deploy via GitHub Integration

1. Push this repository to GitHub.
2. Go to [vercel.com](https://vercel.com) → **New Project** → Import from GitHub.
3. Select `anjanatn/Resume-Parser`.
4. Vercel auto-detects `vercel.json` and deploys automatically.

The `vercel.json` routes all requests to `api/index.py`:

```json
{
  "version": 2,
  "rewrites": [
    { "source": "/(.*)", "destination": "/api/index" }
  ]
}
```

---

## 🔌 REST API Endpoints

### `GET /`
Renders the main web UI with the current count of indexed resumes.

### `POST /api/search`
Search and rank candidates by natural language query.

**Request Body (JSON):**
```json
{
  "query": "Senior Python developer with AWS and Docker",
  "skills": ["Python", "Docker"],
  "min_exp": 3.0,
  "min_degree": "Bachelor's"
}
```

**Response:**
```json
{
  "success": true,
  "count": 5,
  "results": [
    {
      "candidate": {
        "name": "Alex Chen",
        "title": "Senior Python Developer & AI Engineer",
        "experience_years": 5.5,
        "highest_degree": "Bachelor's",
        "skills": ["Python", "FastAPI", "AWS", "Docker", "Kubernetes"],
        "contact": {
          "email": "alex.chen@email.com",
          "phone": "(555) 234-5678",
          "location": "San Francisco, CA"
        }
      },
      "suitability_score": 95.2,
      "match_details": {
        "matched_skills": ["Python", "Docker", "AWS"],
        "missing_skills": [],
        "skill_score_pct": 100.0,
        "exp_score_pct": 100.0
      }
    }
  ]
}
```

### `POST /api/upload`
Upload a new PDF resume (multipart/form-data, field: `file`).

### `GET /api/candidates`
Returns all indexed candidate profiles.

---

## 🧮 Suitability Scoring Model

| Component | Weight | Description |
|---|---|---|
| **Skill Match** | 40% | Fraction of required skills found in candidate profile |
| **Experience Match** | 30% | Years of experience vs. required minimum |
| **Semantic Relevance** | 20% | TF-IDF cosine similarity between query and resume text |
| **Education Level** | 10% | Degree level vs. required minimum |

```
score = (skill_match × 0.40) + (exp_match × 0.30) + (tfidf_similarity × 0.20) + (edu_match × 0.10)
```

---

## 🛠️ Skills Taxonomy (100+ skills)

- **Languages:** Python, Java, JavaScript, TypeScript, C++, Go, Swift, Kotlin, Rust, SQL, Dart, Bash
- **Frontend:** React, Next.js, Vue.js, Angular, HTML5, CSS3, Tailwind CSS, Redux, Sass
- **Backend:** FastAPI, Django, Flask, Spring Boot, Express.js, Node.js, GraphQL, REST APIs, Microservices
- **AI/ML:** PyTorch, TensorFlow, Scikit-Learn, Pandas, NumPy, HuggingFace, NLP, LLMs
- **Cloud/DevOps:** AWS, Azure, GCP, Docker, Kubernetes, Terraform, Ansible, Jenkins, CI/CD
- **Databases:** PostgreSQL, MySQL, MongoDB, Oracle DB, Redis, SQLite
- **Security:** Cybersecurity, Wireshark, SIEM, Penetration Testing, OWASP
- **Tools:** Git, Figma, Flutter, Firebase, JIRA, Tableau, PowerBI, Prometheus, Grafana

---

## 📁 Sample Resumes Included

| # | Candidate | Role |
|---|---|---|
| 1 | Alex Chen | Senior Python Developer & AI Engineer |
| 2 | Maria Garcia | Full-Stack Software Engineer (Python & React) |
| 3 | David Smith | Junior Data Analyst |
| 4 | Priya Sharma | DevOps & Cloud Infrastructure Lead |
| 5 | Jordan Lee | Senior Frontend Engineer |
| 6 | Elena Rostova | Principal Backend Java & Spring Engineer |
| 7 | Dr. Marcus Johnson | Senior Data Scientist & NLP Specialist |
| 8 | Sarah Jenkins | Technical Product Manager & Agile Coach |
| 9 | Liam O'Connor | Cross-Platform Mobile Engineer |
| 10 | Zoe Patel | Cybersecurity & Automation Engineer |

---

## 🧪 Running Tests

```bash
python -m unittest tests/test_system.py -v
```

All 5 tests cover: parsing accuracy, field extraction, Python search ranking, DevOps ranking, and PhD Data Science ranking.

---

## 📦 Dependencies

```
Flask>=3.0.0
reportlab>=4.0.0
pymupdf>=1.23.0
pypdf>=3.17.0
scikit-learn>=1.3.0
```

> **Note:** `streamlit` and `pandas` are needed only for `app.py` (Streamlit UI), not for Flask/Vercel deployment.

---

## 📝 License

MIT License — see [LICENSE](LICENSE) for details.

---

*Built with ❤️ using Python, Flask, PyMuPDF, Scikit-Learn, and ReportLab.*
