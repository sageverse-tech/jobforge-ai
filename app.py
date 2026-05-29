import streamlit as st
from google import genai
from google.genai import types
import json
import re
import PyPDF2
import io

# ─── Page Config ───────────────────────────────────────────────
st.set_page_config(
    page_title="JobForge AI – Smart Job Search",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─── Custom CSS ────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Syne:wght@800;900&family=DM+Sans:wght@400;500;600&display=swap');

html, body, [class*="css"] {
    background-color: #060910 !important;
    color: #c9d1d9 !important;
    font-family: 'DM Sans', sans-serif !important;
}
.stApp { background-color: #060910 !important; }

#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 1.5rem !important; max-width: 1100px !important; }

::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: #0d1117; }
::-webkit-scrollbar-thumb { background: #30363d; border-radius: 3px; }

.stButton > button {
    background: linear-gradient(135deg, #1a3a6a, #0f2a50) !important;
    color: #79c0ff !important;
    border: 1px solid #1f4a7a !important;
    border-radius: 10px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 600 !important;
    padding: 0.6rem 2rem !important;
    transition: all 0.2s !important;
    width: 100% !important;
}
.stButton > button:hover {
    box-shadow: 0 0 25px rgba(88,166,255,0.35) !important;
    border-color: #58a6ff !important;
    color: #fff !important;
    transform: translateY(-1px) !important;
}

.stTextArea textarea, .stTextInput input {
    background: #0d1117 !important;
    color: #c9d1d9 !important;
    border: 1px solid #21262d !important;
    border-radius: 8px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 14px !important;
}

.streamlit-expanderHeader { background: #0a0f1a !important; border: 1px solid #161b22 !important; border-radius: 8px !important; color: #c9d1d9 !important; font-weight: 600 !important; }
.streamlit-expanderContent { background: #0a0f1a !important; border: 1px solid #161b22 !important; border-top: none !important; border-radius: 0 0 8px 8px !important; }
.stSelectbox > div > div { background: #0d1117 !important; border: 1px solid #21262d !important; color: #c9d1d9 !important; border-radius: 8px !important; }
.stProgress > div > div { background: #58a6ff !important; }
hr { border-color: #161b22 !important; }
.stAlert { border-radius: 8px !important; }

.header-box {
    background: linear-gradient(135deg, #0d1117, #0f1e35);
    border: 1px solid #161b22;
    border-radius: 14px;
    padding: 22px 26px;
    margin-bottom: 20px;
}
.tag {
    background: #0d1117;
    color: #58a6ff;
    border: 1px solid #1f3050;
    border-radius: 3px;
    padding: 1px 7px;
    font-size: 11px;
    font-family: 'JetBrains Mono', monospace;
    display: inline-block;
    margin: 2px;
}
</style>
""", unsafe_allow_html=True)

# ─── Helpers ───────────────────────────────────────────────────
def extract_text_from_pdf(pdf_file):
    try:
        reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        return f"Error extracting text: {e}"

def parse_jobs(text: str) -> list:
    text = text.replace("```json", "").replace("```", "").strip()
    s, e = text.find("["), text.rfind("]")
    if s == -1 or e == -1: return []
    try: return json.loads(text[s:e+1])
    except Exception: return []

def search_jobs_with_gemini(query: str, api_key: str, resume_context: str) -> list:
    client = genai.Client(api_key=api_key)
    
    prompt = f"""You are a job search assistant. Search the web for real, current job postings based on the user's query.
Return ONLY a JSON array (no markdown block, no explanation) of up to 6 job objects following this exact structure:
[
  {{
    "title": "exact job title",
    "company": "company name",
    "location": "city or Remote",
    "type": "Internship or Full-time",
    "description": "2-sentence description",
    "tags": ["skill1","skill2","skill3"],
    "applyLink": "direct URL to job posting",
    "source": "LinkedIn or Naukri or Internshala or Company Website",
    "match": 90
  }}
]
Resume context for matching calculation: {resume_context[:800]}

Search Query: {query}"""

    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            tools=[types.Tool(google_search=types.GoogleSearch())]
        )
    )
    return parse_jobs(response.text)

def generate_cover_letter(job: dict, api_key: str, resume_text: str, user_name: str) -> str:
    client = genai.Client(api_key=api_key)
    prompt = f"""Write a highly professional and tailored corporate cover letter for {user_name}.
Job Title: {job.get('title')}
Company: {job.get('company')}
Location: {job.get('location')}
Description: {job.get('description')}
Skills Required: {', '.join(job.get('tags', []))}

Applicant's Resume Data:
{resume_text}

Rules to follow strictly:
1. Max 3 short paragraphs.
2. Maintain a confident, professional, and humble tone.
3. Highlight specific matching projects or experiences from the resume data.
4. Address to "Dear Hiring Manager," and sign off clearly as {user_name} at the end."""

    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt
    )
    return response.text

def dedup(jobs: list) -> list:
    seen = set()
    out = []
    for j in jobs:
        key = f"{j.get('title','').lower()}-{j.get('company','').lower()}"
        if key not in seen:
            seen.add(key)
            out.append(j)
    return sorted(out, key=lambda x: x.get("match", 80), reverse=True)

def match_color(score: int) -> str:
    if score >= 92: return "#00ff88"
    if score >= 85: return "#ffd700"
    return "#ff8c42"

# ─── Session State ─────────────────────────────────────────────
for key, default in [
    ("jobs", []),
    ("selected", None),
    ("cover_letter", ""),
    ("api_key", ""),
    ("resume_text", ""),
    ("user_name", "Applicant"),
    ("searched", False),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ─── Header ────────────────────────────────────────────────────
st.markdown("""
<div class="header-box">
  <div style="display:flex;align-items:center;gap:14px">
    <div style="width:44px;height:44px;background:linear-gradient(135deg,#00ff88,#00b4d8);border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:22px;flex-shrink:0">⚡</div>
    <div>
      <div style="font-family:'Syne',sans-serif;font-size:24px;font-weight:900;color:#fff;letter-spacing:-0.5px">JobForge <span style="color:#00ff88">AI</span></div>
      <div style="font-size:11px;color:#6e7681;font-family:'JetBrains Mono',monospace;margin-top:3px">Your Personal Job Search & Cover Letter Automation Tool</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ─── User Inputs (API, Resume, Search Specs) ───────────────────
with st.expander("⚙️ Step 1: Configure Your Profile (Required)", expanded=not st.session_state.resume_text):
    st.markdown("<div style='font-size:14px;font-weight:600;margin-bottom:10px;color:#79c0ff'>1. Free Gemini Engine Setup</div>", unsafe_allow_html=True)
    api_input = st.text_input("Google Gemini API Key", type="password", placeholder="AIzaSy...", value=st.session_state.api_key)
    if api_input: st.session_state.api_key = api_input
    
    st.markdown("""
    <div style='font-size:11px;color:#6e7681;font-family:"JetBrains Mono",monospace;margin-top:6px'>
    Get your 100% free key → <a href='https://aistudio.google.com/' target='_blank' style='color:#58a6ff'>Google AI Studio</a>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<hr style='margin:15px 0'>", unsafe_allow_html=True)
    
    st.markdown("<div style='font-size:14px;font-weight:600;margin-bottom:10px;color:#79c0ff'>2. Upload Your Resume</div>", unsafe_allow_html=True)
    user_name_input = st.text_input("Your Full Name (for signature)", value=st.session_state.user_name)
    if user_name_input: st.session_state.user_name = user_name_input
    
    uploaded_file = st.file_uploader("Upload PDF Resume", type="pdf")
    if uploaded_file is not None:
        with st.spinner("Reading resume contents..."):
            extracted_text = extract_text_from_pdf(uploaded_file)
            st.session_state.resume_text = extracted_text
            st.success("✓ Resume successfully parsed into app framework!")

st.markdown("<hr>", unsafe_allow_html=True)

# ─── Search Section ────────────────────────────────────────────
col_left, col_right = st.columns([1.1, 1], gap="large")

with col_left:
    st.markdown("""
    <div style='font-family:"Syne",sans-serif;font-size:20px;font-weight:900;color:#fff;margin-bottom:6px'>
      🔍 Step 2: Find Your Dream Job
    </div>
    """, unsafe_allow_html=True)

    job_role = st.text_input("What role are you looking for?", placeholder="e.g. Frontend Developer, Data Analyst, ML Intern")
    location = st.text_input("Location Preference", placeholder="e.g. Remote, Bangalore, Pune")
    filter_type = st.selectbox("Job Schedule", ["Internship", "Full-time", "Any"])

    ready_to_search = st.session_state.api_key and st.session_state.resume_text and job_role

    if st.button("⚡ Search Live Jobs Now", disabled=not ready_to_search):
        all_jobs = []
        progress = st.progress(0, text="Launching live web scanning pipeline...")
        
        type_str = "" if filter_type == "Any" else filter_type
        loc_str = f"in {location}" if location else ""
        query = f"{job_role} {type_str} openings {loc_str} 2026 site:linkedin.com/jobs/view OR site:naukri.com OR site:internshala.com"

        try:
            results = search_jobs_with_gemini(query, st.session_state.api_key, st.session_state.resume_text)
            all_jobs.extend(results)
        except Exception as ex:
            st.warning(f"Search pipeline exception: {ex}")
            
        progress.empty()
        st.session_state.jobs = dedup(all_jobs)
        st.session_state.searched = True
        st.session_state.selected = None
        st.session_state.cover_letter = ""
        st.rerun()

    if not st.session_state.api_key or not st.session_state.resume_text:
        st.markdown("""<div style='font-size:11px;color:#f85149;font-family:"JetBrains Mono",monospace;margin-top:6px'>
        ⚠ Setup your free Gemini API Key and upload your Resume in Step 1 to begin.</div>""", unsafe_allow_html=True)

    # ── Job Results ──
    if st.session_state.jobs:
        jobs = st.session_state.jobs
        st.markdown(f"""
        <div style='display:flex;align-items:center;justify-content:space-between;margin:18px 0 10px'>
          <div style='font-size:13px;font-weight:600;color:#fff'>{len(jobs)} Verified Matches Found</div>
          <div style='font-size:11px;color:#6e7681;font-family:"JetBrains Mono",monospace'>ranked by compatibility index</div>
        </div>
        """, unsafe_allow_html=True)

        for i, job in enumerate(jobs):
            score = job.get("match", 80)
            color = match_color(score)
            source = job.get("source", "Web Resource")
            sc = "#79c0ff" if "LinkedIn" in source else "#ffa657" if "Naukri" in source else "#56d364"

            with st.expander(f"{'🟢' if score>=92 else '🟡' if score>=85 else '🟠'} {job.get('title','Job Post')} — {job.get('company','N/A')}", expanded=False):
                c1, c2 = st.columns([2, 1])
                with c1:
                    st.markdown(f"""
                    <div style='font-size:12px;color:#8b949e;margin-bottom:6px'>
                      <span style='color:{sc};font-family:"JetBrains Mono",monospace;font-size:10px'>{source}</span>
                      &nbsp;•&nbsp; {job.get('location','N/A')}
                      &nbsp;•&nbsp; <span style='color:#56d364'>{job.get('type','N/A')}</span>
                    </div>
                    <div style='font-size:12px;color:#6e7681;line-height:1.6;margin-bottom:10px'>{job.get('description','No details extracted.')}</div>
                    """, unsafe_allow_html=True)
                with c2:
                    st.markdown(f"""
                    <div style='text-align:right'>
                      <div style='font-size:28px;font-weight:900;color:{color};font-family:"JetBrains Mono",monospace'>{score}%</div>
                      <div style='font-size:10px;color:#6e7681'>match profile</div>
                    </div>
                    """, unsafe_allow_html=True)

                if job.get("applyLink"):
                    st.markdown(f"""
                    <a href="{job['applyLink']}" target="_blank" style="display:block;background:#0f1a2a;border:1px solid #1f3a5c;border-radius:8px;padding:10px;text-decoration:none;color:#79c0ff;font-size:12px;text-align:center;margin-bottom:10px">
                      ↗ Apply on official portal
                    </a>
                    """, unsafe_allow_html=True)

                if st.button(f"✍ Build Custom Cover Letter", key=f"gen_{i}"):
                    with st.spinner("Gemini is reading matching profile criteria..."):
                        try:
                            letter = generate_cover_letter(job, st.session_state.api_key, st.session_state.resume_text, st.session_state.user_name)
                            st.session_state.selected = job
                            st.session_state.cover_letter = letter
                            st.rerun()
                        except Exception as ex:
                            st.error(f"Generation error: {ex}")

# ─── Right Column: Cover Letter Panel ─────────────────────────
with col_right:
    if st.session_state.selected and st.session_state.cover_letter:
        job = st.session_state.selected

        st.markdown(f"""
        <div style='background:#0f1e35;border:1px solid #1f4a7a;border-radius:12px;padding:16px 18px;margin-bottom:16px'>
          <div style='font-size:14px;font-weight:700;color:#fff'>Generated context for: {job.get('title')}</div>
          <div style='font-size:12px;color:#79c0ff;margin-top:4px'>{job.get('company')}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""<div style='font-size:11px;color:#56d364;font-family:"JetBrains Mono",monospace;margin-bottom:8px'>✓ Document successfully rendered</div>""", unsafe_allow_html=True)
        st.text_area("Cover Letter", value=st.session_state.cover_letter, height=280, key="cover_display", label_visibility="collapsed")

        email_draft = f"Subject: Application for position: {job.get('title')} — {st.session_state.user_name}\n\n{st.session_state.cover_letter}\n\n---\nSincerely,\n{st.session_state.user_name}\n📎 Attachment: Resume.pdf"
        st.markdown("""<div style='font-size:11px;color:#79c0ff;font-family:"JetBrains Mono",monospace;margin:14px 0 8px'>📧 Email Structure (Copy Format)</div>""", unsafe_allow_html=True)
        st.text_area("Email Draft", value=email_draft, height=200, key="email_display", label_visibility="collapsed")

    else:
        st.markdown("""
        <div style='background:#0a0f1a;border:1px solid #161b22;border-radius:12px;padding:40px 24px;text-align:center;margin-top:40px'>
          <div style='font-size:32px;margin-bottom:14px'>📝</div>
          <div style='font-size:14px;font-weight:600;color:#fff;margin-bottom:8px'>Automation Studio Workspace</div>
          <div style='font-size:12px;color:#6e7681;line-height:1.7'>
            When you choose a target job record from the search layout, click on <b>Build Custom Cover Letter</b>. The Gemini orchestration layer will build your dynamic pitch workspace instantly.
          </div>
        </div>
        """, unsafe_allow_html=True)

# ─── Footer ───────────────────────────────────────────────────
st.markdown("""
<hr>
<div style='text-align:center;font-size:10px;color:#21262d;font-family:"JetBrains Mono",monospace;padding:10px'>
  JobForge AI v2.0 • Public SaaS Architecture • Free Gemini Pipeline Tier
</div>
""", unsafe_allow_html=True)
