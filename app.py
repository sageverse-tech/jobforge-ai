import streamlit as st
import anthropic
import json
import re

# ─── Page Config ───────────────────────────────────────────────
st.set_page_config(
    page_title="JobForge AI – Khushraj Varghat",
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

/* Hide default Streamlit elements */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 1.5rem !important; max-width: 1100px !important; }

/* Scrollbar */
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: #0d1117; }
::-webkit-scrollbar-thumb { background: #30363d; border-radius: 3px; }

/* Buttons */
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

/* Text area */
.stTextArea textarea {
    background: #0d1117 !important;
    color: #c9d1d9 !important;
    border: 1px solid #21262d !important;
    border-radius: 8px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 13px !important;
}

/* Expander */
.streamlit-expanderHeader {
    background: #0a0f1a !important;
    border: 1px solid #161b22 !important;
    border-radius: 8px !important;
    color: #c9d1d9 !important;
    font-weight: 600 !important;
}
.streamlit-expanderContent {
    background: #0a0f1a !important;
    border: 1px solid #161b22 !important;
    border-top: none !important;
    border-radius: 0 0 8px 8px !important;
}

/* Selectbox */
.stSelectbox > div > div {
    background: #0d1117 !important;
    border: 1px solid #21262d !important;
    color: #c9d1d9 !important;
    border-radius: 8px !important;
}

/* Progress bar */
.stProgress > div > div { background: #58a6ff !important; }

/* Divider */
hr { border-color: #161b22 !important; }

/* Metric */
[data-testid="metric-container"] {
    background: #0a0f1a;
    border: 1px solid #161b22;
    border-radius: 10px;
    padding: 14px 18px;
}
[data-testid="stMetricValue"] { color: #79c0ff !important; font-family: 'JetBrains Mono', monospace !important; font-size: 22px !important; }
[data-testid="stMetricLabel"] { color: #6e7681 !important; font-size: 11px !important; }

/* Info/success/warning boxes */
.stAlert { border-radius: 8px !important; }

/* Copy button area */
.copy-box {
    background: #0d1117;
    border: 1px solid #21262d;
    border-radius: 8px;
    padding: 14px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;
    white-space: pre-wrap;
    line-height: 1.7;
    color: #c9d1d9;
    max-height: 320px;
    overflow-y: auto;
}

.header-box {
    background: linear-gradient(135deg, #0d1117, #0f1e35);
    border: 1px solid #161b22;
    border-radius: 14px;
    padding: 22px 26px;
    margin-bottom: 20px;
}

.job-card {
    background: #0a0f1a;
    border: 1px solid #161b22;
    border-radius: 10px;
    padding: 16px 18px;
    margin-bottom: 10px;
    transition: all 0.2s;
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

# ─── Resume ────────────────────────────────────────────────────
RESUME_TEXT = """KHUSHRAJ VARGHAT
AI/ML Engineer | BTech CS (AI/ML) | KK Modi University, Bhilai
LinkedIn: linkedin.com/in/khushraj-varghat-bb5709292
CGPA: 8.05 | 3rd Year Student (2022–2026)

TECHNICAL SKILLS:
- Machine Learning: Scikit-learn, TensorFlow, PyTorch, Gradient Boosting, CNN, ViT
- Computer Vision: OpenCV, MediaPipe, YOLOv8
- Programming: Python (advanced), OOP, Data Structures & Algorithms
- Cloud & DevOps: AWS, Azure, Flask, Git
- Cybersecurity: Kali Linux, Wireshark, ARP Spoofing, Metasploitable, Nmap
- Deployment: Hugging Face Spaces, Streamlit Cloud

KEY PROJECTS:
1. Salary Prediction Model — AICTE/Edunet Internship
   Gradient Boosting, 88% accuracy, end-to-end ML pipeline

2. Deepfake Detection System — Global Hackathon 8th/250+ teams
   CNN + Vision Transformer (ViT), 85%+ accuracy

3. Gesture-Controlled Music System
   OpenCV + MediaPipe, 95% accuracy, 400ms→100ms response optimization

EXPERIENCE:
- Virtual Internship: AICTE implemented by Edunet Foundation (AI/ML domain)
- Hackathon: 8th place globally at Shankar College Jaipur (250+ teams)

EDUCATION:
BTech Computer Science (AI/ML Specialization)
KK Modi University, Bhilai | 2022–2026 | CGPA: 8.05"""

SEARCH_QUERIES = [
    ("LinkedIn / Naukri / Internshala", "AI ML intern fresher jobs India 2026 site:linkedin.com OR site:naukri.com OR site:internshala.com"),
    ("Computer Vision & Deep Learning", "computer vision deep learning internship India 2026 apply now"),
    ("ML Engineer Fresher Roles", "machine learning engineer fresher job India 2026 TensorFlow PyTorch"),
    ("Data Science Internships", "data science internship India remote 2026 Python stipend"),
]

# ─── Helpers ───────────────────────────────────────────────────
def parse_jobs(text: str) -> list:
    text = re.sub(r"```json|```", "", text).strip()
    s, e = text.find("["), text.rfind("]")
    if s == -1 or e == -1:
        return []
    try:
        return json.loads(text[s:e+1])
    except Exception:
        return []


def search_jobs_with_claude(query: str, api_key: str) -> list:
    client = anthropic.Anthropic(api_key=api_key)
    system = f"""You are a job search assistant. Search the web for real, current job postings.
Return ONLY a JSON array (no markdown, no explanation) of up to 6 job objects:
{{
  "title": "exact job title",
  "company": "company name",
  "location": "city or Remote",
  "type": "Internship or Full-time",
  "description": "2-sentence description",
  "tags": ["skill1","skill2","skill3"],
  "applyLink": "direct URL to job posting",
  "source": "LinkedIn or Naukri or Internshala or Company Website",
  "match": <integer 75-99 based on resume fit>
}}
Resume context: {RESUME_TEXT[:500]}
Return ONLY valid JSON array."""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        system=system,
        messages=[{"role": "user", "content": f"Search for real jobs: {query}. Return JSON array only."}],
    )
    text = "".join(b.text for b in response.content if hasattr(b, "text"))
    return parse_jobs(text)


def generate_cover_letter(job: dict, api_key: str) -> str:
    client = anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        messages=[{"role": "user", "content": f"""Write a professional cover letter.
Job Title: {job.get('title')}
Company: {job.get('company')}
Location: {job.get('location')}
Description: {job.get('description')}
Skills: {', '.join(job.get('tags', []))}

Resume:
{RESUME_TEXT}

Rules: 3 paragraphs max, confident tone, highlight relevant projects, sign as Khushraj Varghat, start with Dear Hiring Manager,"""}],
    )
    return response.content[0].text


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
      <div style="font-size:11px;color:#6e7681;font-family:'JetBrains Mono',monospace;margin-top:3px">Real-time job search • AI-powered cover letters • Built for Khushraj Varghat</div>
    </div>
    <div style="margin-left:auto;text-align:right">
      <div style="font-size:11px;color:#56d364;font-family:'JetBrains Mono',monospace">✓ Resume Loaded</div>
      <div style="font-size:10px;color:#6e7681;margin-top:3px;font-family:'JetBrains Mono',monospace">8th / 250+ Hackathon 🏆</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ─── API Key Input ─────────────────────────────────────────────
with st.expander("🔑 Enter Anthropic API Key (required once per session)", expanded=not st.session_state.api_key):
    api_input = st.text_input(
        "Anthropic API Key",
        type="password",
        placeholder="sk-ant-...",
        value=st.session_state.api_key,
        help="Get your free key at console.anthropic.com",
    )
    if api_input:
        st.session_state.api_key = api_input
        st.success("✓ API key saved for this session!")
    st.markdown("""
    <div style='font-size:11px;color:#6e7681;font-family:"JetBrains Mono",monospace;margin-top:6px'>
    Get free key → <a href='https://console.anthropic.com' target='_blank' style='color:#58a6ff'>console.anthropic.com</a>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)

# ─── Search Section ────────────────────────────────────────────
col_left, col_right = st.columns([1.1, 1], gap="large")

with col_left:
    st.markdown("""
    <div style='font-family:"Syne",sans-serif;font-size:20px;font-weight:900;color:#fff;margin-bottom:6px'>
      🔍 Find Real-Time AI/ML Jobs
    </div>
    <div style='font-size:12px;color:#6e7681;margin-bottom:18px'>
      Searches LinkedIn, Naukri, Internshala & company sites simultaneously
    </div>
    """, unsafe_allow_html=True)

    filter_type = st.selectbox("Filter by type", ["All", "Internship", "Full-time"], label_visibility="collapsed")

    if st.button("⚡ Search Live Jobs Now", disabled=not st.session_state.api_key):
        all_jobs = []
        progress = st.progress(0, text="Starting search...")
        status = st.empty()

        for i, (label, query) in enumerate(SEARCH_QUERIES):
            status.markdown(f"""
            <div style='background:#0f1e35;border:1px solid #1f4a7a;border-radius:8px;padding:10px 16px;
                        font-family:"JetBrains Mono",monospace;font-size:12px;color:#79c0ff'>
              ⟳ Scanning: {label}...
            </div>
            """, unsafe_allow_html=True)
            try:
                results = search_jobs_with_claude(query, st.session_state.api_key)
                all_jobs.extend(results)
            except Exception as ex:
                st.warning(f"Search {i+1} error: {ex}")
            progress.progress((i + 1) / len(SEARCH_QUERIES), text=f"Completed {i+1}/{len(SEARCH_QUERIES)} searches")

        progress.empty()
        status.empty()
        st.session_state.jobs = dedup(all_jobs)
        st.session_state.searched = True
        st.session_state.selected = None
        st.session_state.cover_letter = ""
        st.rerun()

    if not st.session_state.api_key:
        st.markdown("""<div style='font-size:11px;color:#f85149;font-family:"JetBrains Mono",monospace;margin-top:6px'>
        ⚠ Enter API key above to enable search</div>""", unsafe_allow_html=True)

    # ── Job Results ──
    if st.session_state.jobs:
        jobs = st.session_state.jobs
        if filter_type != "All":
            jobs = [j for j in jobs if j.get("type") == filter_type]

        st.markdown(f"""
        <div style='display:flex;align-items:center;justify-content:space-between;margin:18px 0 10px'>
          <div style='font-size:13px;font-weight:600;color:#fff'>{len(jobs)} Jobs Found</div>
          <div style='font-size:11px;color:#6e7681;font-family:"JetBrains Mono",monospace'>sorted by resume match %</div>
        </div>
        """, unsafe_allow_html=True)

        for i, job in enumerate(jobs):
            score = job.get("match", 80)
            color = match_color(score)
            source = job.get("source", "")
            source_colors = {
                "LinkedIn": "#79c0ff", "Naukri": "#ffa657",
                "Internshala": "#56d364", "Company Website": "#d2a8ff",
            }
            sc = source_colors.get(source, "#8b949e")

            with st.expander(f"{'🟢' if score>=92 else '🟡' if score>=85 else '🟠'} {job.get('title','N/A')} — {job.get('company','N/A')}  ({score}% match)", expanded=False):
                c1, c2 = st.columns([2, 1])
                with c1:
                    st.markdown(f"""
                    <div style='font-size:12px;color:#8b949e;margin-bottom:6px'>
                      <span style='color:{sc};font-family:"JetBrains Mono",monospace;font-size:10px'>{source}</span>
                      &nbsp;•&nbsp; {job.get('location','N/A')}
                      &nbsp;•&nbsp; <span style='color:#56d364'>{job.get('type','N/A')}</span>
                    </div>
                    <div style='font-size:12px;color:#6e7681;line-height:1.6;margin-bottom:10px'>{job.get('description','')}</div>
                    <div style='display:flex;gap:5px;flex-wrap:wrap'>
                      {''.join(f"<span class='tag'>{t}</span>" for t in job.get('tags',[])[:4])}
                    </div>
                    """, unsafe_allow_html=True)
                with c2:
                    st.markdown(f"""
                    <div style='text-align:right'>
                      <div style='font-size:28px;font-weight:900;color:{color};font-family:"JetBrains Mono",monospace'>{score}%</div>
                      <div style='font-size:10px;color:#6e7681'>resume match</div>
                    </div>
                    """, unsafe_allow_html=True)

                # Apply Link
                if job.get("applyLink"):
                    st.markdown(f"""
                    <a href="{job['applyLink']}" target="_blank" style="
                      display:block;background:#0f1a2a;border:1px solid #1f3a5c;border-radius:8px;
                      padding:10px 14px;text-decoration:none;color:#79c0ff;font-size:12px;
                      font-weight:600;margin-bottom:10px;text-align:center">
                      ↗ Apply Directly — {job.get('source','Open Link')}
                    </a>
                    """, unsafe_allow_html=True)

                # Generate Cover Letter Button
                btn_key = f"gen_{i}_{job.get('company','')}"
                if st.button(f"✍ Generate Cover Letter for {job.get('company','')}", key=btn_key):
                    if not st.session_state.api_key:
                        st.error("Add API key first!")
                    else:
                        with st.spinner("AI is writing your personalized cover letter..."):
                            try:
                                letter = generate_cover_letter(job, st.session_state.api_key)
                                st.session_state.selected = job
                                st.session_state.cover_letter = letter
                                st.rerun()
                            except Exception as ex:
                                st.error(f"Error: {ex}")

# ─── Right Column: Cover Letter Panel ─────────────────────────
with col_right:
    if st.session_state.selected and st.session_state.cover_letter:
        job = st.session_state.selected

        st.markdown(f"""
        <div style='background:#0f1e35;border:1px solid #1f4a7a;border-radius:12px;padding:16px 18px;margin-bottom:16px'>
          <div style='font-size:14px;font-weight:700;color:#fff'>{job.get('title')}</div>
          <div style='font-size:12px;color:#79c0ff;margin-top:4px'>{job.get('company')} • {job.get('location')}</div>
        </div>
        """, unsafe_allow_html=True)

        # Cover Letter Box
        st.markdown("""
        <div style='font-size:11px;color:#56d364;font-family:"JetBrains Mono",monospace;margin-bottom:8px'>
          ✓ cover_letter.txt — AI Generated
        </div>
        """, unsafe_allow_html=True)

        st.text_area(
            "Cover Letter",
            value=st.session_state.cover_letter,
            height=280,
            key="cover_display",
            label_visibility="collapsed",
        )

        # Email Draft
        email_draft = f"""Subject: Application for {job.get('title')} — Khushraj Varghat

{st.session_state.cover_letter}

---
📎 Attachment: Khushraj_Varghat_Resume.pdf"""

        st.markdown("""
        <div style='font-size:11px;color:#79c0ff;font-family:"JetBrains Mono",monospace;margin:14px 0 8px'>
          📧 Full Email Draft (copy & paste into Gmail/Outlook)
        </div>
        """, unsafe_allow_html=True)

        st.text_area(
            "Email Draft",
            value=email_draft,
            height=200,
            key="email_display",
            label_visibility="collapsed",
        )

        # Steps
        st.markdown("""
        <div style='background:#0f2a1a;border:1px solid #2a5a2a;border-radius:8px;padding:14px 16px;
                    font-size:12px;color:#56d364;font-family:"JetBrains Mono",monospace;line-height:1.9;margin-top:12px'>
          ✓ Select all text in "Email Draft" above → Copy<br>
          → Open Gmail / Outlook<br>
          → Paste in email body<br>
          → Attach: Khushraj_Varghat_Resume.pdf<br>
          → Hit Send 🚀
        </div>
        """, unsafe_allow_html=True)

        # Regenerate
        if st.button("↺ Regenerate Cover Letter", key="regen"):
            with st.spinner("Regenerating..."):
                try:
                    st.session_state.cover_letter = generate_cover_letter(job, st.session_state.api_key)
                    st.rerun()
                except Exception as ex:
                    st.error(f"Error: {ex}")

    else:
        st.markdown("""
        <div style='background:#0a0f1a;border:1px solid #161b22;border-radius:12px;padding:40px 24px;text-align:center;margin-top:10px'>
          <div style='font-size:32px;margin-bottom:14px'>✍</div>
          <div style='font-size:14px;font-weight:600;color:#fff;margin-bottom:8px'>Cover Letter will appear here</div>
          <div style='font-size:12px;color:#6e7681;line-height:1.7'>
            1. Enter API key above<br>
            2. Search live jobs<br>
            3. Click "Generate Cover Letter" on any job<br>
            4. AI writes a personalized letter instantly!
          </div>
        </div>
        """, unsafe_allow_html=True)

# ─── Footer ───────────────────────────────────────────────────
st.markdown("""
<hr>
<div style='text-align:center;font-size:10px;color:#21262d;font-family:"JetBrains Mono",monospace;padding:10px'>
  JobForge AI v2 • Real-time search • Powered by Claude • Built for khushraj.varghat
</div>
""", unsafe_allow_html=True)
