from flask import Flask, render_template, request, jsonify
import os
import sys
import io
import urllib.request
from urllib.parse import urlparse
import re

# Ensure root directory is on python path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.parser import ResumeParser
from src.search_engine import IntelligentSearchEngine
from src.notifier import send_hr_email_alert, dispatch_n8n_event
from db.database import (
    init_db, save_candidate, get_all_candidates,
    update_candidate_status, find_duplicate, compute_content_hash,
    get_dashboard_metrics
)

app = Flask(__name__, template_folder=os.path.join(BASE_DIR, 'templates'), static_folder=os.path.join(BASE_DIR, 'static'))

parser = ResumeParser()
init_db()

def bootstrap_initial_resumes():
    """Seed SQLite DB from ResumeParserUnlocked/ if DB is empty."""
    existing = get_all_candidates()
    if existing:
        return existing
        
    candidates = []
    unlock_dir = os.path.join(BASE_DIR, "ResumeParserUnlocked")
    if os.path.exists(unlock_dir):
        for fname in sorted(os.listdir(unlock_dir)):
            if fname.lower().endswith((".pdf", ".docx", ".txt")) and not fname.startswith("._"):
                fpath = os.path.join(unlock_dir, fname)
                try:
                    parsed = parser.parse(fpath, filename=fname)
                    save_candidate(parsed)
                    candidates.append(parsed)
                except Exception as e:
                    print(f"[WARN] Could not parse {fname}: {e}")
                    
    # Fallback to data/resumes if ResumeParserUnlocked is empty
    if not candidates:
        resumes_dir = os.path.join(BASE_DIR, "data", "resumes")
        if os.path.exists(resumes_dir):
            for fname in sorted(os.listdir(resumes_dir)):
                if fname.lower().endswith((".pdf", ".docx", ".txt")):
                    fpath = os.path.join(resumes_dir, fname)
                    parsed = parser.parse(fpath, filename=fname)
                    save_candidate(parsed)
                    candidates.append(parsed)
                    
    return get_all_candidates()

candidates_db = bootstrap_initial_resumes()
search_engine = IntelligentSearchEngine(candidates_db)

@app.route('/')
def index():
    all_cands = get_all_candidates()
    return render_template('index.html', candidate_count=len(all_cands))

@app.route('/api/search', methods=['POST'])
def search_api():
    data = request.get_json() or {}
    query = data.get('query', '')
    filter_skills = data.get('skills', [])
    min_exp = float(data.get('min_exp', 0.0))
    min_degree = data.get('min_degree', 'Any')
    
    # Reload fresh candidate state from DB
    current_candidates = get_all_candidates()
    search_engine.set_candidates(current_candidates)
    
    results = search_engine.search(
        query=query,
        filter_skills=filter_skills,
        min_experience=min_exp,
        min_degree=min_degree
    )
    return jsonify({"success": True, "count": len(results), "results": results})

@app.route('/api/match_jd', methods=['POST'])
def match_jd_api():
    data = request.get_json() or {}
    jd_text = data.get('jd_text', '').strip()
    if not jd_text:
        return jsonify({"success": False, "error": "No Job Description text provided"}), 400

    current_candidates = get_all_candidates()
    search_engine.set_candidates(current_candidates)
    match_data = search_engine.match_job_description(jd_text)
    
    # Check if any top candidate scored >= 80% to alert HR
    if match_data["results"]:
        top_match = match_data["results"][0]
        if top_match["suitability_score"] >= 80.0:
            send_hr_email_alert(top_match["candidate"], top_match["suitability_score"], target_role="Job Description Match")
            dispatch_n8n_event("HIGH_MATCH_FOUND", {
                "candidate": top_match["candidate"]["name"],
                "score": top_match["suitability_score"],
                "role": "Job Description Match"
            })
            
    return jsonify({
        "success": True,
        "jd_requirements": match_data["jd_requirements"],
        "count": len(match_data["results"]),
        "results": match_data["results"]
    })

@app.route('/api/upload', methods=['POST'])
def upload_api():
    if 'file' not in request.files:
        return jsonify({"success": False, "error": "No file attached"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"success": False, "error": "No selected file"}), 400
    
    try:
        parsed = parser.parse(file, filename=file.filename)
        
        # Check duplicate
        content_hash = compute_content_hash(parsed.get("raw_text", ""))
        existing_dup, dup_type = find_duplicate(
            content_hash,
            name=parsed.get("name"),
            email=parsed.get("contact", {}).get("email")
        )
        
        is_duplicate = False
        dup_msg = ""
        if existing_dup:
            is_duplicate = True
            dup_msg = f"Duplicate detected ({dup_type}): Candidate already exists as '{existing_dup['name']}'."
        
        save_candidate(parsed)
        all_cands = get_all_candidates()
        search_engine.set_candidates(all_cands)
        
        # Notify n8n
        dispatch_n8n_event("RESUME_INGESTED", {
            "candidate_id": parsed["id"],
            "name": parsed["name"],
            "skills": parsed["skills"],
            "experience_years": parsed["experience_years"],
            "is_duplicate": is_duplicate
        })
        
        return jsonify({
            "success": True,
            "candidate": parsed,
            "total": len(all_cands),
            "is_duplicate": is_duplicate,
            "duplicate_message": dup_msg
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/upload_url', methods=['POST'])
def upload_url_api():
    data = request.get_json() or {}
    raw_url = data.get('url', '').strip()
    if not raw_url:
        return jsonify({"success": False, "error": "No URL provided"}), 400

    url = raw_url
    gdrive_match = re.search(r'drive\.google\.com/(?:file/d/([a-zA-Z0-9_-]+)|open\?id=([a-zA-Z0-9_-]+))', url)
    if gdrive_match:
        file_id = gdrive_match.group(1) or gdrive_match.group(2)
        url = f"https://drive.google.com/uc?export=download&id={file_id}"
    elif "dropbox.com" in url:
        if "dl=0" in url:
            url = url.replace("dl=0", "dl=1")
        elif "dl=1" not in url and "raw=1" not in url:
            url = f"{url}&dl=1" if "?" in url else f"{url}?dl=1"

    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        )
        with urllib.request.urlopen(req, timeout=15) as response:
            file_bytes = response.read()

        if not file_bytes:
            return jsonify({"success": False, "error": "Downloaded file is empty"}), 400

        path = urlparse(raw_url).path
        filename = os.path.basename(path) or "document.pdf"
        if not filename.lower().endswith((".pdf", ".docx", ".txt")):
            filename = f"{filename}.pdf"

        parsed = parser.parse(io.BytesIO(file_bytes), filename=filename)
        
        # Check duplicate
        content_hash = compute_content_hash(parsed.get("raw_text", ""))
        existing_dup, dup_type = find_duplicate(
            content_hash,
            name=parsed.get("name"),
            email=parsed.get("contact", {}).get("email")
        )
        
        is_duplicate = False
        dup_msg = ""
        if existing_dup:
            is_duplicate = True
            dup_msg = f"Duplicate detected ({dup_type}): Candidate already exists as '{existing_dup['name']}'."

        save_candidate(parsed)
        all_cands = get_all_candidates()
        search_engine.set_candidates(all_cands)
        
        dispatch_n8n_event("RESUME_INGESTED_VIA_URL", {
            "candidate_id": parsed["id"],
            "name": parsed["name"],
            "url": raw_url,
            "is_duplicate": is_duplicate
        })
        
        return jsonify({
            "success": True,
            "candidate": parsed,
            "total": len(all_cands),
            "is_duplicate": is_duplicate,
            "duplicate_message": dup_msg
        })
    except Exception as e:
        return jsonify({"success": False, "error": f"Failed to fetch or parse document link: {str(e)}"}), 500

@app.route('/api/webhook', methods=['POST'])
def webhook_api():
    """
    Inbound webhook for n8n automation and external HR systems.
    Accepts:
      - JSON with raw_text, base64 PDF, or resume URL
      - Triggers parsing, storage, ranking, and notification.
    """
    import base64
    data = request.get_json() or {}
    
    # 1. URL mode
    if "url" in data:
        try:
            req = urllib.request.Request(data["url"], headers={"User-Agent": "Resume-Parser-n8n"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                b = resp.read()
            parsed = parser.parse(io.BytesIO(b), filename=data.get("filename", "webhook_resume.pdf"))
        except Exception as ex:
            return jsonify({"success": False, "error": f"Webhook URL download failed: {ex}"}), 400
            
    # 2. Base64 file mode
    elif "file_base64" in data:
        try:
            file_bytes = base64.b64decode(data["file_base64"])
            parsed = parser.parse(io.BytesIO(file_bytes), filename=data.get("filename", "webhook_resume.pdf"))
        except Exception as ex:
            return jsonify({"success": False, "error": f"Base64 decode failed: {ex}"}), 400
            
    # 3. Direct raw text mode
    elif "raw_text" in data:
        parsed = parser.parse(data["raw_text"], filename=data.get("filename", "webhook_text.txt"))
    else:
        return jsonify({"success": False, "error": "Invalid webhook payload. Provide 'url', 'file_base64', or 'raw_text'"}), 400
        
    content_hash = compute_content_hash(parsed.get("raw_text", ""))
    existing_dup, dup_type = find_duplicate(content_hash, parsed.get("name"), parsed.get("contact", {}).get("email"))
    
    save_candidate(parsed)
    all_cands = get_all_candidates()
    search_engine.set_candidates(all_cands)
    
    # Optional evaluation against a target JD or query provided in webhook
    match_result = None
    if "target_jd" in data:
        jd_match = search_engine.match_job_description(data["target_jd"])
        for r in jd_match["results"]:
            if r["candidate"]["id"] == parsed["id"]:
                match_result = r
                if r["suitability_score"] >= 80.0:
                    send_hr_email_alert(parsed, r["suitability_score"], target_role="n8n Target JD")
                break
                
    return jsonify({
        "success": True,
        "candidate": parsed,
        "is_duplicate": bool(existing_dup),
        "match_result": match_result,
        "total_indexed": len(all_cands)
    })

@app.route('/api/update_status', methods=['POST'])
def update_status_api():
    data = request.get_json() or {}
    cand_id = data.get('id', '')
    new_status = data.get('status', 'New')

    # Allowed pipeline statuses
    allowed_statuses = ["New", "Shortlisted", "Interview", "Interview Scheduled", "Hired", "Rejected", "Archived"]
    if new_status not in allowed_statuses:
        return jsonify({"success": False, "error": f"Invalid status: {new_status}"}), 400

    update_candidate_status(cand_id, new_status)
    all_cands = get_all_candidates()
    search_engine.set_candidates(all_cands)
    
    # Notify n8n of status transition
    dispatch_n8n_event("CANDIDATE_STATUS_CHANGED", {
        "candidate_id": cand_id,
        "status": new_status
    })
    
    return jsonify({"success": True, "id": cand_id, "status": new_status})

@app.route('/api/dashboard_stats', methods=['GET'])
def dashboard_stats_api():
    stats = get_dashboard_metrics()
    return jsonify({"success": True, "data": stats})

@app.route('/api/candidates', methods=['GET'])
def get_candidates():
    cands = get_all_candidates()
    return jsonify({"success": True, "candidates": cands})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
