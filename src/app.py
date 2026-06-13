import sys
from pathlib import Path

# Add project root to python search path
sys.path.append(str(Path(__file__).resolve().parent.parent))

import streamlit as st
import tempfile
import os
import pandas as pd
from src.pipeline import ResumeMatchPipeline
from src.vector_store import LocalVectorStore
from src.config import UPLOAD_DIR

# Set Page Config
st.set_page_config(
    page_title="Resume Match AI",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling (Glassmorphism & Rich Colors)
st.markdown("""
<style>
    /* Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    /* Main Background & Title Styling */
    .main {
        background-color: #0f172a;
        color: #f8fafc;
    }
    
    h1 {
        background: linear-gradient(135deg, #a5b4fc 0%, #6366f1 50%, #4338ca 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700;
        margin-bottom: 2rem;
    }
    
    /* Cards and Glassmorphism */
    .card {
        background: rgba(30, 41, 59, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
        backdrop-filter: blur(5px);
        -webkit-backdrop-filter: blur(5px);
    }
    
    /* Badge styling */
    .badge {
        display: inline-block;
        padding: 0.25em 0.6em;
        font-size: 0.85em;
        font-weight: 600;
        line-height: 1;
        text-align: center;
        white-space: nowrap;
        vertical-align: baseline;
        border-radius: 30px;
        margin: 2px;
    }
    
    .badge-match {
        background-color: rgba(16, 185, 129, 0.2);
        color: #10b981;
        border: 1px solid rgba(16, 185, 129, 0.3);
    }
    
    .badge-missing {
        background-color: rgba(239, 68, 68, 0.2);
        color: #ef4444;
        border: 1px solid rgba(239, 68, 68, 0.3);
    }
    
    .badge-additional {
        background-color: rgba(59, 130, 246, 0.2);
        color: #3b82f6;
        border: 1px solid rgba(59, 130, 246, 0.3);
    }
    
    /* Radial custom bar */
    .score-container {
        display: flex;
        align-items: center;
        gap: 15px;
    }
    
    .score-bar {
        background-color: #334155;
        border-radius: 10px;
        height: 12px;
        width: 100%;
        overflow: hidden;
    }
    
    .score-fill {
        height: 100%;
        border-radius: 10px;
        background: linear-gradient(90deg, #6366f1 0%, #06b6d4 100%);
        transition: width 0.5s ease-in-out;
    }
    
    /* Custom button styles */
    .stButton>button {
        background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
        color: white;
        border: none;
        padding: 0.5rem 2rem;
        border-radius: 8px;
        font-weight: 600;
        transition: transform 0.2s ease;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
    }
</style>
""", unsafe_allow_html=True)

# Initialize Pipeline
@st.cache_resource
def get_pipeline():
    return ResumeMatchPipeline()

pipeline = get_pipeline()

# App Header
st.markdown("<h1>🎯 Resume Match AI</h1>", unsafe_allow_html=True)
st.write("An intelligent resume ingestion and match analysis system powered by semantic similarity and keyword analysis.")

# Layout Columns
col_main, col_sidebar = st.columns([7, 3])

with col_sidebar:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("📁 Database Management")
    
    # Ingest Resumes
    uploaded_files = st.file_uploader(
        "Upload Resumes",
        type=["pdf", "docx", "txt"],
        accept_multiple_files=True,
        key="resume_uploader"
    )
    
    if uploaded_files:
        for uploaded_file in uploaded_files:
            # Check if already processed
            already_uploaded = False
            for doc in pipeline.vector_store.documents:
                # Basic check by filename
                pass # Just check if the file is already processed in list
                
            # Create a unique temporary directory to avoid name collisions on Windows
            temp_dir = tempfile.mkdtemp()
            tmp_path = Path(temp_dir) / uploaded_file.name
            
            try:
                # Write the file directly with its original filename
                with open(tmp_path, "wb") as f:
                    f.write(uploaded_file.getvalue())
                
                with st.spinner(f"Ingesting {uploaded_file.name}..."):
                    pipeline.ingest_resume(tmp_path)
                st.success(f"Successfully uploaded: {uploaded_file.name}")
            except Exception as e:
                st.error(f"Failed to process {uploaded_file.name}: {e}")
            finally:
                # Clean up the temporary file and directory
                try:
                    if tmp_path.exists():
                        tmp_path.unlink()
                    os.rmdir(temp_dir)
                except Exception as cleanup_error:
                    pass
                
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Active Resumes list
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("📄 Stored Resumes")
    
    if pipeline.vector_store.documents:
        # Create a table showing resumes
        resume_data = []
        for i, (doc_id, meta) in enumerate(zip(pipeline.vector_store.ids, pipeline.vector_store.metadatas)):
            resume_data.append({
                "ID": doc_id,
                "Candidate": meta.get("candidate_name", "Unknown"),
                "Filename": meta.get("filename", "Unknown")
            })
        
        df = pd.DataFrame(resume_data)
        st.dataframe(df[["Candidate", "Filename"]], use_container_width=True)
        
        # Select delete options
        to_delete = st.selectbox("Select Resume to Delete", df["Candidate"].tolist())
        if st.button("Delete Selected"):
            row = df[df["Candidate"] == to_delete].iloc[0]
            del_id = row["ID"]
            if pipeline.delete_resume(del_id):
                st.toast(f"Deleted {to_delete}'s resume.")
                st.rerun()
    else:
        st.info("No resumes stored in database yet. Upload a few to begin!")
    st.markdown('</div>', unsafe_allow_html=True)


with col_main:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("💼 Job Description input")
    
    # Input Job Description
    jd_input = st.text_area(
        "Paste Job Description text here...",
        height=200,
        placeholder="We are looking for a Senior Python Developer with experience in FastAPI, Docker, and AWS...",
        key="jd_text"
    )
    
    top_n = st.slider("Max candidate matches to show", 1, 10, 5)
    
    match_clicked = st.button("💡 Analyze & Match Resumes")
    st.markdown('</div>', unsafe_allow_html=True)
    
    if match_clicked or jd_input:
        if not jd_input.strip():
            st.warning("Please provide a Job Description to run the analysis.")
        elif not pipeline.vector_store.documents:
            st.warning("Please upload at least one resume in the sidebar before matching.")
        else:
            with st.spinner("Analyzing matching elements..."):
                results = pipeline.match_resumes(jd_input, top_k=top_n)
            
            if not results:
                st.info("No matches found.")
            else:
                st.subheader(f"📊 Match Analysis Results ({len(results)} matches)")
                
                for r in results:
                    candidate = r["candidate_name"]
                    email = r["email"] or "Not provided"
                    phone = r["phone"] or "Not provided"
                    analysis = r["analysis"]
                    score = analysis["match_score"]
                    sem_similarity = analysis["semantic_similarity"]
                    skill_ratio = analysis["skill_match_ratio"]
                    
                    # Custom container/card for candidate match
                    st.markdown(f"""
                    <div class="card">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                            <h3 style="margin: 0; color: #a5b4fc;">👤 {candidate}</h3>
                            <span style="font-size: 1.2em; font-weight: bold; color: #06b6d4;">{score}% Match</span>
                        </div>
                        <div style="font-size: 0.9em; color: #94a3b8; margin-bottom: 15px;">
                            ✉️ <b>Email:</b> {email} &nbsp;|&nbsp; 📞 <b>Phone:</b> {phone} &nbsp;|&nbsp; 📄 <b>File:</b> {r['filename']}
                        </div>
                        <div class="score-container" style="margin-bottom: 15px;">
                            <span style="min-width: 150px; font-size: 0.9em;">Overall Alignment</span>
                            <div class="score-bar">
                                <div class="score-fill" style="width: {score}%;"></div>
                            </div>
                        </div>
                        <div style="display: flex; gap: 20px; font-size: 0.9em; margin-bottom: 20px;">
                            <div>🧠 Semantic Agreement: <b>{sem_similarity}%</b></div>
                            <div>🛠️ Core Skill Overlap: <b>{skill_ratio}%</b></div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # Streamlit expander for details
                    with st.expander("🔍 Detailed Feedback & Skill Gap Analysis"):
                        # Show matched/missing skills
                        st.write("#### Skill Classifications")
                        
                        # Render badges
                        matched_badges = "".join([f'<span class="badge badge-match">{s}</span>' for s in analysis["matched_skills"]])
                        missing_badges = "".join([f'<span class="badge badge-missing">{s}</span>' for s in analysis["missing_skills"]])
                        additional_badges = "".join([f'<span class="badge badge-additional">{s}</span>' for s in analysis["additional_skills"]])
                        
                        st.markdown(f"**Matched Core Skills:**<br>{matched_badges if matched_badges else '*None identified*'}", unsafe_allow_html=True)
                        st.markdown(f"<div style='margin-top: 10px;'><b>Missing Requested Skills:</b><br>{missing_badges if missing_badges else '*None (Perfect Match!)*'}</div>", unsafe_allow_html=True)
                        st.markdown(f"<div style='margin-top: 10px;'><b>Additional Related Skills:</b><br>{additional_badges if additional_badges else '*None identified*'}</div>", unsafe_allow_html=True)
                        
                        st.write("---")
                        
                        # Strengths, Gaps, Recommendations
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write("**💪 Strengths & Alignment**")
                            for strength in analysis["strengths"]:
                                st.markdown(f"- ✅ {strength}")
                            if not analysis["strengths"]:
                                st.write("- No notable strengths identified.")
                                
                            st.write("<br>**⚠️ Identified Skill Gaps**", unsafe_allow_html=True)
                            for gap in analysis["gaps"]:
                                st.markdown(f"- 🔍 {gap}")
                            if not analysis["gaps"]:
                                st.write("- No critical skill gaps identified.")
                                
                        with col2:
                            st.write("**💡 Recommendations to Resume**")
                            for rec in analysis["recommendations"]:
                                st.markdown(f"- 📌 {rec}")
                            if not analysis["recommendations"]:
                                st.write("- No special recommendations.")
                    
                    st.markdown("</div>", unsafe_allow_html=True)
