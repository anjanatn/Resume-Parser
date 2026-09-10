import sqlite3
import json
import os
import hashlib
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "db", "resumes.db")

def get_db_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Candidates table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS candidates (
        id TEXT PRIMARY KEY,
        anonymous_id TEXT,
        filename TEXT,
        name TEXT,
        title TEXT,
        email TEXT,
        phone TEXT,
        location TEXT,
        linkedin TEXT,
        github TEXT,
        skills TEXT, -- JSON array
        experience_years REAL,
        highest_degree TEXT,
        education TEXT, -- JSON array
        work_history TEXT, -- JSON array
        raw_text TEXT,
        summary_pitch TEXT,
        status TEXT DEFAULT 'New',
        content_hash TEXT UNIQUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Events table for n8n audit and notifications
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_type TEXT,
        candidate_id TEXT,
        details TEXT, -- JSON object
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    conn.commit()
    conn.close()

def compute_content_hash(text):
    """Compute SHA-256 hash of clean text for duplicate detection."""
    if not text:
        return ""
    # Normalize whitespace for consistent hashing
    normalized = " ".join(text.strip().lower().split())
    return hashlib.sha256(normalized.encode('utf-8')).hexdigest()

def find_duplicate(content_hash, name=None, email=None):
    """Check if candidate already exists by content hash or email."""
    if not content_hash and not email:
        return None, None
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check by exact content hash first
    if content_hash:
        cursor.execute("SELECT * FROM candidates WHERE content_hash = ?", (content_hash,))
        row = cursor.fetchone()
        if row:
            conn.close()
            return dict(row), "exact_content"
            
    # Check by non-placeholder email
    if email and email != "N/A" and "@" in email:
        cursor.execute("SELECT * FROM candidates WHERE email = ?", (email,))
        row = cursor.fetchone()
        if row:
            conn.close()
            return dict(row), "email_match"
            
    conn.close()
    return None, None

def save_candidate(cand_dict):
    """Insert or update candidate in SQLite DB."""
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    content_hash = compute_content_hash(cand_dict.get("raw_text", ""))
    
    contact = cand_dict.get("contact", {})
    skills_json = json.dumps(cand_dict.get("skills", []))
    education_json = json.dumps(cand_dict.get("education", []))
    work_history_json = json.dumps(cand_dict.get("work_history", []))
    
    cursor.execute("""
    INSERT INTO candidates (
        id, anonymous_id, filename, name, title,
        email, phone, location, linkedin, github,
        skills, experience_years, highest_degree,
        education, work_history, raw_text, summary_pitch,
        status, content_hash, updated_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    ON CONFLICT(id) DO UPDATE SET
        filename=excluded.filename,
        name=excluded.name,
        title=excluded.title,
        email=excluded.email,
        phone=excluded.phone,
        location=excluded.location,
        linkedin=excluded.linkedin,
        github=excluded.github,
        skills=excluded.skills,
        experience_years=excluded.experience_years,
        highest_degree=excluded.highest_degree,
        education=excluded.education,
        work_history=excluded.work_history,
        raw_text=excluded.raw_text,
        summary_pitch=excluded.summary_pitch,
        status=excluded.status,
        content_hash=excluded.content_hash,
        updated_at=CURRENT_TIMESTAMP
    """, (
        cand_dict.get("id"),
        cand_dict.get("anonymous_id"),
        cand_dict.get("filename"),
        cand_dict.get("name"),
        cand_dict.get("title"),
        contact.get("email", "N/A"),
        contact.get("phone", "N/A"),
        contact.get("location", "Not specified"),
        contact.get("linkedin", "N/A"),
        contact.get("github", "N/A"),
        skills_json,
        cand_dict.get("experience_years", 0.0),
        cand_dict.get("highest_degree", "None"),
        education_json,
        work_history_json,
        cand_dict.get("raw_text", ""),
        cand_dict.get("summary_pitch", ""),
        cand_dict.get("status", "New"),
        content_hash
    ))
    
    # Log event
    cursor.execute("INSERT INTO events (event_type, candidate_id, details) VALUES (?, ?, ?)", (
        "CANDIDATE_SAVED",
        cand_dict.get("id"),
        json.dumps({"name": cand_dict.get("name"), "status": cand_dict.get("status", "New")})
    ))
    
    conn.commit()
    conn.close()

def get_all_candidates():
    """Retrieve all candidates formatted as standard candidate dictionaries."""
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM candidates ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    
    candidates = []
    for r in rows:
        cand = {
            "id": r["id"],
            "anonymous_id": r["anonymous_id"],
            "filename": r["filename"],
            "name": r["name"],
            "title": r["title"],
            "contact": {
                "email": r["email"],
                "phone": r["phone"],
                "location": r["location"],
                "linkedin": r["linkedin"],
                "github": r["github"]
            },
            "skills": json.loads(r["skills"]) if r["skills"] else [],
            "experience_years": r["experience_years"],
            "highest_degree": r["highest_degree"],
            "education": json.loads(r["education"]) if r["education"] else [],
            "work_history": json.loads(r["work_history"]) if r["work_history"] else [],
            "raw_text": r["raw_text"],
            "summary_pitch": r["summary_pitch"],
            "status": r["status"] or "New",
            "content_hash": r["content_hash"]
        }
        candidates.append(cand)
    return candidates

def update_candidate_status(cand_id, new_status):
    """Update candidate pipeline status (New, Shortlisted, Interview, Hired, Rejected)."""
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE candidates SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?
    """, (new_status, cand_id))
    
    cursor.execute("INSERT INTO events (event_type, candidate_id, details) VALUES (?, ?, ?)", (
        "STATUS_UPDATED",
        cand_id,
        json.dumps({"new_status": new_status})
    ))
    
    conn.commit()
    conn.close()

def get_dashboard_metrics():
    """Aggregate all statistics needed for the Chart.js Dashboard."""
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Total count
    cursor.execute("SELECT COUNT(*) as total FROM candidates")
    total_candidates = cursor.fetchone()["total"]
    
    # Status breakdown
    cursor.execute("SELECT status, COUNT(*) as count FROM candidates GROUP BY status")
    status_rows = cursor.fetchall()
    status_counts = {
        "New": 0, "Shortlisted": 0, "Interview": 0, "Hired": 0, "Rejected": 0
    }
    for r in status_rows:
        s = r["status"]
        if "interview" in s.lower():
            status_counts["Interview"] += r["count"]
        elif s in status_counts:
            status_counts[s] += r["count"]
        else:
            status_counts["New"] += r["count"]
            
    # Degree breakdown
    cursor.execute("SELECT highest_degree, COUNT(*) as count FROM candidates GROUP BY highest_degree")
    degree_rows = cursor.fetchall()
    degree_counts = {r["highest_degree"]: r["count"] for r in degree_rows}
    
    # Experience ranges
    cursor.execute("""
    SELECT
        SUM(CASE WHEN experience_years < 2 THEN 1 ELSE 0 END) as exp_0_2,
        SUM(CASE WHEN experience_years >= 2 AND experience_years < 5 THEN 1 ELSE 0 END) as exp_2_5,
        SUM(CASE WHEN experience_years >= 5 AND experience_years < 8 THEN 1 ELSE 0 END) as exp_5_8,
        SUM(CASE WHEN experience_years >= 8 THEN 1 ELSE 0 END) as exp_8_plus,
        AVG(experience_years) as avg_exp
    FROM candidates
    """)
    exp_row = cursor.fetchone()
    exp_distribution = {
        "0-2 Yrs (Entry)": exp_row["exp_0_2"] or 0,
        "2-5 Yrs (Mid)": exp_row["exp_2_5"] or 0,
        "5-8 Yrs (Senior)": exp_row["exp_5_8"] or 0,
        "8+ Yrs (Staff)": exp_row["exp_8_plus"] or 0
    }
    avg_experience = round(exp_row["avg_exp"] or 0.0, 1)
    
    # Skills frequency
    cursor.execute("SELECT skills FROM candidates")
    skills_rows = cursor.fetchall()
    skill_freq = {}
    for r in skills_rows:
        if r["skills"]:
            skills_list = json.loads(r["skills"])
            for s in skills_list:
                skill_freq[s] = skill_freq.get(s, 0) + 1
                
    # Sort top 15 skills
    top_skills = sorted(skill_freq.items(), key=lambda x: x[1], reverse=True)[:15]
    
    # Recent activity
    cursor.execute("SELECT name, title, status, highest_degree, experience_years, created_at FROM candidates ORDER BY created_at DESC LIMIT 6")
    recent_candidates = [dict(r) for r in cursor.fetchall()]
    
    conn.close()
    
    return {
        "total_candidates": total_candidates,
        "shortlisted_count": status_counts.get("Shortlisted", 0),
        "hired_count": status_counts.get("Hired", 0),
        "avg_experience": avg_experience,
        "status_breakdown": status_counts,
        "degree_breakdown": degree_counts,
        "experience_breakdown": exp_distribution,
        "top_skills": dict(top_skills),
        "recent_candidates": recent_candidates
    }
