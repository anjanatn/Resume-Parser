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
    if os.path.exists(resumes_dir):
        for fname in sorted(os.listdir(resumes_dir)):
            if fname.endswith(".pdf"):
                fpath = os.path.join(resumes_dir, fname)
                parsed = parser.parse(fpath, filename=fname)
                candidates.append(parsed)
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

@app.route('/api/candidates', methods=['GET'])
def get_candidates():
    return jsonify({"success": True, "candidates": candidates_db})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
