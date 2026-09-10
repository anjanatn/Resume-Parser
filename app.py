import os
import tempfile
import json
import pandas as pd
import streamlit as st

from src.parser import ResumeParser
from src.search_engine import IntelligentSearchEngine

# Page Config
st.set_page_config(
    page_title="AI Resume Parser & Intelligent Search",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #4B5563;
        margin-bottom: 1.5rem;
    }
    .candidate-card {
        background-color: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 10px;
        padding: 1.2rem;
        margin-bottom: 1rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }
    .score-badge-high {
        background-color: #DEF7EC;
        color: #03543F;
        font-weight: bold;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 1rem;
    }
    .score-badge-med {
        background-color: #E1EFFE;
        color: #1E429F;
        font-weight: bold;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 1rem;
    }
    .score-badge-low {
        background-color: #FFE8E8;
        color: #9B1C1C;
        font-weight: bold;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 1rem;
    }
    .skill-tag {
        display: inline-block;
        background-color: #EDF2F7;
        color: #2D3748;
        font-size: 0.82rem;
        padding: 0.2rem 0.5rem;
        border-radius: 5px;
        margin-right: 0.3rem;
        margin-bottom: 0.3rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session State
if "candidates" not in st.session_state:
    st.session_state.candidates = []

if "search_engine" not in st.session_state:
    st.session_state.search_engine = IntelligentSearchEngine()

@st.cache_resource
def load_default_resumes():
    parser = ResumeParser()
    resumes_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "data/resumes"))
    parsed_list = []
    if os.path.exists(resumes_dir):
        for filename in sorted(os.listdir(resumes_dir)):
            if filename.endswith(".pdf"):
                fpath = os.path.join(resumes_dir, filename)
                parsed = parser.parse(fpath, filename=filename)
                parsed_list.append(parsed)
    return parsed_list

# Load initial resumes if empty
if not st.session_state.candidates:
    default_candidates = load_default_resumes()
    st.session_state.candidates = default_candidates
    st.session_state.search_engine.set_candidates(default_candidates)

# Header
st.markdown('<div class="main-header">🚀 Sarah\'s Resume Parser & Candidate Matcher</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Automated PDF Parsing • Key Information Extraction • Intelligent Natural Query Search & Suitability Ranking</div>', unsafe_allow_html=True)

# Sidebar - Resume Management & Controls
with st.sidebar:
    st.image("https://img.icons8.com/color/96/resume.png", width=70)
    st.title("Recruiter Controls")
    
    st.subheader("📤 Upload New Resumes")
    uploaded_files = st.file_uploader("Upload PDF Resumes", type=["pdf"], accept_multiple_files=True)
    
    if uploaded_files:
        parser = ResumeParser()
        new_count = 0
        for uploaded_file in uploaded_files:
            # Check if already added
            if not any(c.get("filename") == uploaded_file.name for c in st.session_state.candidates):
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    tmp.write(uploaded_file.read())
                    tmp_path = tmp.name
                
                parsed = parser.parse(tmp_path, filename=uploaded_file.name)
                st.session_state.candidates.append(parsed)
                new_count += 1
                os.unlink(tmp_path)
        
        if new_count > 0:
            st.session_state.search_engine.set_candidates(st.session_state.candidates)
            st.success(f"Successfully processed {new_count} new resume(s)!")

    st.markdown("---")
    st.metric("Total Resumes Indexed", len(st.session_state.candidates))
    
    # Collect all unique skills for sidebar filter
    all_skills = set()
    for c in st.session_state.candidates:
        all_skills.update(c.get("skills", []))
    all_skills = sorted(list(all_skills))

    st.subheader("🎯 Faceted Search Filters")
    selected_skills = st.multiselect("Filter by Skills", options=all_skills)
    min_exp_slider = st.slider("Minimum Experience (Years)", min_value=0.0, max_value=10.0, value=0.0, step=0.5)
    selected_degree = st.selectbox("Minimum Education Level", ["Any", "Bachelor's", "Master's", "PhD"])

    if st.button("🔄 Reset Filters"):
        st.experimental_rerun()

# Main Search Tabs
tab1, tab2, tab3 = st.tabs(["🔍 Candidate Search & Ranking", "📊 Candidate Database Overview", "⚡ Batch Export"])

with tab1:
    col_q1, col_q2 = st.columns([4, 1])
    
    with col_q1:
        query = st.text_input("Enter natural language search query:", value="Python developers with 3+ years experience", placeholder="e.g. Senior DevOps engineer with AWS & Kubernetes")
    
    with col_q2:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        sample_btn = st.button("Try Sample Query")
        if sample_btn:
            query = "Python developers with 3+ years experience"

    # Quick suggestion chips
    st.markdown("<b>Quick Search Examples:</b>", unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    if c1.button("🐍 Python Devs (3+ yrs)"):
        query = "Python developers with 3+ years experience"
    if c2.button("☁️ DevOps & AWS"):
        query = "DevOps AWS Kubernetes Terraform"
    if c3.button("🤖 Data Science & PhD"):
        query = "Data Scientist PyTorch PhD"
    if c4.button("💻 Full Stack React"):
        query = "Full-Stack Python React Developer"

    # Execute Search
    results = st.session_state.search_engine.search(
        query=query,
        filter_skills=selected_skills,
        min_experience=min_exp_slider,
        min_degree=selected_degree
    )

    st.markdown(f"### 🎯 Search Results ({len(results)} Candidates Ranked by Suitability)")

    if not results:
        st.info("No candidates found matching the specified criteria. Try adjusting your filters.")
    else:
        for idx, res in enumerate(results, 1):
            cand = res["candidate"]
            score = res["suitability_score"]
            match_det = res["match_details"]
            
            # Badge style
            if score >= 80:
                badge_class = "score-badge-high"
            elif score >= 60:
                badge_class = "score-badge-med"
            else:
                badge_class = "score-badge-low"

            with st.container():
                col_info, col_score = st.columns([4, 1])
                
                with col_info:
                    st.markdown(f"#### #{idx} {cand['name']} — *{cand['title']}*")
                    
                    # Contact row
                    cnt = cand["contact"]
                    contact_bits = [f"📧 {cnt['email']}", f"📞 {cnt['phone']}", f"📍 {cnt['location']}"]
                    if cnt.get("github") != "N/A":
                        contact_bits.append(f"🔗 {cnt['github']}")
                    if cnt.get("linkedin") != "N/A":
                        contact_bits.append(f"💼 {cnt['linkedin']}")
                    
                    st.markdown(f"<small>{' | '.join(contact_bits)}</small>", unsafe_allow_html=True)
                    
                    # Highlights
                    st.markdown(f"**Experience:** `{cand['experience_years']} Years` | **Highest Degree:** `{cand['highest_degree']}`")
                    
                    # Skills Badges
                    skills_html = "".join([f"<span class='skill-tag'>{s}</span>" for s in cand["skills"]])
                    st.markdown(f"**Skills:** {skills_html}", unsafe_allow_html=True)
                
                with col_score:
                    st.markdown(f"<div style='text-align: center; margin-top: 10px;'><span class='{badge_class}'>{score}% Match</span></div>", unsafe_allow_html=True)
                    st.markdown(f"<div style='font-size: 0.8rem; text-align: center; margin-top: 5px;'>Skill Match: {match_det['skill_score_pct']}%<br>Exp Match: {match_det['exp_score_pct']}%</div>", unsafe_allow_html=True)

                # Full Profile Expander
                with st.expander(f"Inspect Full Candidate Profile & Raw Resume ({cand['name']})"):
                    col_m1, col_m2 = st.columns(2)
                    with col_m1:
                        st.write("##### 📌 Extracted Key Details")
                        st.json({
                            "Name": cand["name"],
                            "Title": cand["title"],
                            "Total Experience": f"{cand['experience_years']} Years",
                            "Highest Degree": cand["highest_degree"],
                            "Contact Info": cand["contact"],
                            "Matched Skills": match_det["matched_skills"],
                            "Missing Skills": match_det["missing_skills"]
                        })
                    with col_m2:
                        st.write("##### 📜 Raw Parsed Resume Document")
                        st.text_area("Resume Text", value=cand["raw_text"], height=250, key=f"text_{cand['id']}_{idx}")
                
                st.markdown("<hr style='margin: 1rem 0;'>", unsafe_allow_html=True)

with tab2:
    st.subheader("📋 Candidate Roster Overview")
    
    table_data = []
    for c in st.session_state.candidates:
        table_data.append({
            "Name": c["name"],
            "Title": c["title"],
            "Experience (Yrs)": c["experience_years"],
            "Degree": c["highest_degree"],
            "Skills": ", ".join(c["skills"][:6]) + ("..." if len(c["skills"]) > 6 else ""),
            "Email": c["contact"]["email"],
            "Phone": c["contact"]["phone"],
            "Location": c["contact"]["location"]
        })
    
    df_overview = pd.DataFrame(table_data)
    st.dataframe(df_overview, use_container_width=True)

with tab3:
    st.subheader("📥 Export Candidate Search Report")
    st.write("Export parsed candidate database and search scores for Sarah and HR team.")
    
    col_exp1, col_exp2 = st.columns(2)
    
    # Export JSON
    json_str = json.dumps(st.session_state.candidates, indent=2)
    col_exp1.download_button(
        label="Download Full Candidates Database (JSON)",
        data=json_str,
        file_name="candidate_resumes_database.json",
        mime="application/json"
    )
    
    # Export CSV
    csv_data = pd.DataFrame([
        {
            "Name": c["name"],
            "Title": c["title"],
            "ExperienceYears": c["experience_years"],
            "HighestDegree": c["highest_degree"],
            "Skills": "; ".join(c["skills"]),
            "Email": c["contact"]["email"],
            "Phone": c["contact"]["phone"],
            "Location": c["contact"]["location"]
        } for c in st.session_state.candidates
    ]).to_csv(index=False)
    
    col_exp2.download_button(
        label="Download Candidates Table (CSV)",
        data=csv_data,
        file_name="candidate_resumes_table.csv",
        mime="text/csv"
    )
