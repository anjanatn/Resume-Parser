from flask import Flask, render_template, request, jsonify
import os
import sys

# Ensure root directory is on python path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.parser import ResumeParser
from src.search_engine import IntelligentSearchEngine

app = Flask(__name__, template_folder=os.path.join(BASE_DIR, 'templates'), static_folder=os.path.join(BASE_DIR, 'static'))

parser = ResumeParser()
resumes_dir = os.path.join(BASE_DIR, "data", "resumes")

def load_initial_candidates():
    candidates = []
    # Load synthetic resumes from data/resumes/
    if os.path.exists(resumes_dir):
        for fname in sorted(os.listdir(resumes_dir)):
            if fname.lower().endswith((".pdf", ".docx", ".txt")):
                fpath = os.path.join(resumes_dir, fname)
                parsed = parser.parse(fpath, filename=fname)
                candidates.append(parsed)
    # Load real resumes from ResumeParserUnlocked/ (skip macOS metadata files)
    unlock_dir = os.path.join(BASE_DIR, "ResumeParserUnlocked")
    if os.path.exists(unlock_dir):
        for fname in sorted(os.listdir(unlock_dir)):
            if fname.lower().endswith((".pdf", ".docx", ".txt")) and not fname.startswith("._"):
                fpath = os.path.join(unlock_dir, fname)
                try:
                    parsed = parser.parse(fpath, filename=fname)
                    candidates.append(parsed)
                except Exception as e:
                    print(f"[WARN] Could not parse {fname}: {e}")
    return candidates

candidates_db = load_initial_candidates()
search_engine = IntelligentSearchEngine(candidates_db)

@app.route('/')
def index():
    return render_template('index.html', candidate_count=len(candidates_db))

@app.route('/api/search', methods=['POST'])
def search_api():
    data = request.get_json() or {}
    query = data.get('query', '')
    filter_skills = data.get('skills', [])
    min_exp = float(data.get('min_exp', 0.0))
    min_degree = data.get('min_degree', 'Any')
    
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

    match_data = search_engine.match_job_description(jd_text)
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
        candidates_db.append(parsed)
        search_engine.set_candidates(candidates_db)
        return jsonify({"success": True, "candidate": parsed, "total": len(candidates_db)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/upload_url', methods=['POST'])
def upload_url_api():
    import urllib.request
    import io
    import re
    from urllib.parse import urlparse

    data = request.get_json() or {}
    raw_url = data.get('url', '').strip()
    if not raw_url:
        return jsonify({"success": False, "error": "No URL provided"}), 400

    # Normalize URLs for common cloud storage services (Google Drive, Dropbox)
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
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
        )
        with urllib.request.urlopen(req, timeout=15) as response:
            file_bytes = response.read()

        if not file_bytes:
            return jsonify({"success": False, "error": "Downloaded file is empty"}), 400

        # Infer filename from URL
        path = urlparse(raw_url).path
        filename = os.path.basename(path) or "document.pdf"
        if not filename.lower().endswith((".pdf", ".docx", ".txt")):
            filename = f"{filename}.pdf"

        parsed = parser.parse(io.BytesIO(file_bytes), filename=filename)
        candidates_db.append(parsed)
        search_engine.set_candidates(candidates_db)
        return jsonify({"success": True, "candidate": parsed, "total": len(candidates_db)})
    except Exception as e:
        return jsonify({"success": False, "error": f"Failed to fetch or parse document link: {str(e)}"}), 500

@app.route('/api/update_status', methods=['POST'])
def update_status_api():
    data = request.get_json() or {}
    cand_id = data.get('id', '')
    new_status = data.get('status', 'New')

    found = False
    for c in candidates_db:
        if c.get('id') == cand_id:
            c['status'] = new_status
            found = True
            break

    if found:
        search_engine.set_candidates(candidates_db)
        return jsonify({"success": True, "id": cand_id, "status": new_status})
    return jsonify({"success": False, "error": "Candidate not found"}), 404

@app.route('/api/candidates', methods=['GET'])
def get_candidates():
    return jsonify({"success": True, "candidates": candidates_db})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
