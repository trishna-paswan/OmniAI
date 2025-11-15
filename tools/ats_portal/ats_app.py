# tools/ats_portal/ats_portal.py
# -*- coding: utf-8 -*-
"""
ATS Resume Analyzer Portal (Admin + User history)
Part of OMNI_AI Unified Suite
"""

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import gradio as gr
import json, os, re, string, hashlib, binascii
from collections import Counter
from PyPDF2 import PdfReader
import docx2txt
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "resume_portal_db.json")

# -------------------------
# Password hashing utilities
# -------------------------
def hash_password(password: str, salt: bytes = None):
    if salt is None:
        salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 200000)
    return binascii.hexlify(salt).decode(), binascii.hexlify(dk).decode()

def verify_password(stored_salt_hex: str, stored_hash_hex: str, password_attempt: str) -> bool:
    salt = binascii.unhexlify(stored_salt_hex.encode())
    attempt_hash = hashlib.pbkdf2_hmac("sha256", password_attempt.encode("utf-8"), salt, 200000)
    return binascii.hexlify(attempt_hash).decode() == stored_hash_hex

# -------------------------
# DB helpers
# -------------------------
def load_db():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, "w") as f:
            json.dump({}, f)
    with open(DB_FILE, "r") as f:
        try:
            return json.load(f)
        except:
            return {}

def save_db(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=2)

def ensure_admin():
    db = load_db()
    if "admin" not in db:
        salt, h = hash_password("adminpass")
        db["admin"] = {
            "salt": salt,
            "pw_hash": h,
            "default_resume": None,
            "history": []
        }
        save_db(db)
ensure_admin()

# -------------------------
# Text utilities
# -------------------------
def extract_text_from_pdf(path):
    try:
        reader = PdfReader(path)
        return " ".join([p.extract_text() or "" for p in reader.pages])
    except:
        return ""

def extract_text_from_docx(path):
    try:
        return docx2txt.process(path) or ""
    except:
        return ""

def clean_text(text):
    if not text: return ""
    t = text.lower()
    t = re.sub(r'\d+', ' ', t)
    t = t.translate(str.maketrans('', '', string.punctuation))
    return t

def get_keywords(text, top_n=30):
    txt = clean_text(text)
    if not txt: return []
    stopwords = set([
        "and","or","the","a","an","of","to","for","in","on","with","by","at","as","from",
        "is","are","be","this","that","will","can","must","should","we","our","you","your"
    ])
    words = [w for w in txt.split() if w not in stopwords and len(w) > 1]
    freq = Counter(words)
    return [w for w,_ in freq.most_common(top_n)]

def calculate_ats_score(resume_text, job_text):
    if not resume_text or not job_text:
        return 0.0
    vectorizer = TfidfVectorizer()
    tfidf = vectorizer.fit_transform([clean_text(resume_text), clean_text(job_text)])
    sim = cosine_similarity(tfidf[0:1], tfidf[1:2])[0,0]
    return round(sim * 100, 2)

def find_missing_keywords(resume_text, job_text):
    rkw = set(get_keywords(resume_text, 60))
    jkw = set(get_keywords(job_text, 60))
    return sorted(list(jkw - rkw))

# -------------------------
# Suggestion logic
# -------------------------
def generate_suggestions(resume_text, job_text):
    suggestions = []
    r = (resume_text or "").lower()
    j = (job_text or "").lower()

    sections = ["education","experience","skills","projects","certifications","summary"]
    for s in [s for s in sections if s not in r]:
        suggestions.append(f"Consider adding or improving your '{s.title()}' section.")

    if len(resume_text or "") < 450:
        suggestions.append("Resume appears short — expand on projects, responsibilities, and results.")
    elif len(resume_text or "") > 3500:
        suggestions.append("Resume appears long — condense to 1–2 pages and focus on relevance.")

    strong_verbs = ["led","developed","designed","implemented","managed","created","analyzed","optimized"]
    if not any(v in r for v in strong_verbs):
        suggestions.append("Use action verbs to emphasize impact.")

    missing = find_missing_keywords(resume_text, job_text)
    if missing:
        suggestions.append("Include keywords such as: " + ", ".join(missing[:8]))

    if "@" not in r:
        suggestions.append("Add a professional email address near the top.")

    if not any(x in r for x in ["linkedin","github","portfolio"]):
        suggestions.append("Add LinkedIn/GitHub/portfolio links.")

    return suggestions or ["Your resume aligns well with the job description."]

# -------------------------
# Auth and logic
# -------------------------
def register_or_login(username, password):
    if not username or not password:
        return False, "Username and password required."

    db = load_db()
    if username in db:
        u = db[username]
        if verify_password(u["salt"], u["pw_hash"], password):
            return True, "Login successful."
        else:
            return False, "Incorrect password."
    else:
        salt, h = hash_password(password)
        db[username] = {"salt": salt, "pw_hash": h, "default_resume": None, "history": []}
        save_db(db)
        return True, "Account created."

def analyze_action(session, username, resume_file, set_default, job_desc, about_role, save_analysis):
    if not username: return ("Username required.", "", "", "")
    if not job_desc: return ("Job description required.", "", "", "")

    db = load_db()
    resume_text = ""
    resume_filename = None

    if resume_file:
        fname = getattr(resume_file, "name", "")
        resume_filename = os.path.basename(fname)

        if fname.lower().endswith(".pdf"):
            resume_text = extract_text_from_pdf(fname)
        elif fname.lower().endswith(".docx"):
            resume_text = extract_text_from_docx(fname)
        else:
            return ("Unsupported file type.", "", "", "")

        if set_default:
            db[username]["default_resume"] = resume_text
            save_db(db)

    else:
        if db.get(username, {}).get("default_resume"):
            resume_text = db[username]["default_resume"]
        else:
            return ("No resume uploaded and no default found.", "", "", "")

    full_job_text = job_desc + ("\n" + about_role if about_role else "")
    score = calculate_ats_score(resume_text, full_job_text)
    missing = find_missing_keywords(resume_text, full_job_text)
    suggestions = generate_suggestions(resume_text, full_job_text)

    if save_analysis:
        db[username]["history"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "ats_score": score,
            "missing_keywords": missing,
            "suggestions": suggestions,
            "resume_filename": resume_filename
        })
        save_db(db)

    return (
        "Analysis complete.",
        f"### ⭐ ATS Score: **{score}/100**",
        f"### 🔍 Missing Keywords:\n{', '.join(missing) or 'None'}",
        "### 📝 Suggestions:\n" + "\n".join(suggestions)
    )

# -------------------------
# Modern Glassmorphism UI (Updated)
# -------------------------
css = """
body, .gradio-container {
    background: #0d1117 !important;
    color: #e6edf3 !important;
    font-family: 'Inter', sans-serif !important;
}

.card {
    backdrop-filter: blur(14px);
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.12);
    padding: 22px;
    border-radius: 18px;
    margin-bottom: 18px;
}

.gr-button {
    background: linear-gradient(135deg, #00e0ff, #0077ff) !important;
    color: black !important;
    border-radius: 12px !important;
    font-weight: 700 !important;
    padding: 12px !important;
}

input, textarea {
    background: rgba(255,255,255,0.07) !important;
    border-radius: 10px !important;
}

"""

with gr.Blocks(css=css, title="ATS Resume Analyzer • OMNI_AI") as ats_app:
    
    session = gr.State({})

    # LOGIN PAGE
    with gr.Column(visible=True) as login_panel:
        gr.Markdown("<h1 style='text-align:center;'>🔐 ATS Portal Login</h1>")
        with gr.Column(elem_classes=["card"]):
            login_user = gr.Textbox(label="Username")
            login_pw = gr.Textbox(label="Password", type="password")
            login_msg = gr.Markdown()
            login_btn = gr.Button("Login / Register")

    # MAIN PORTAL
    with gr.Column(visible=False) as main_panel:
        gr.Markdown("<h1 style='text-align:center;'>📄 ATS Resume Analyzer</h1>")

        with gr.Row():
            with gr.Column(elem_classes=["card"]):
                username_in = gr.Textbox(label="Username")

                resume_file = gr.File(label="Upload Resume", file_types=[".pdf", ".docx"])
                set_default = gr.Checkbox(label="Set as default resume?")
                save_analysis = gr.Checkbox(label="Save this analysis?")

            with gr.Column(elem_classes=["card"]):
                job_desc = gr.Textbox(label="Job Description", lines=6)
                about_role = gr.Textbox(label="About the Role", lines=3)
                analyze_btn = gr.Button("Analyze Resume")

        with gr.Column(elem_classes=["card"]):
            home_status = gr.Markdown()
            home_score = gr.Markdown()
            home_missing = gr.Markdown()
            home_suggestions = gr.Markdown()

    def login_handler(session, username, password):
        success, msg = register_or_login(username, password)
        if success:
            session.update({"username": username})
            return (
                gr.update(visible=False),
                gr.update(visible=True),
                gr.update(value=f"### {msg} — Welcome **{username}**"),
                session
            )
        return (
            gr.update(visible=True),
            gr.update(visible=False),
            gr.update(value=msg),
            session
        )

    login_btn.click(
        fn=login_handler,
        inputs=[session, login_user, login_pw],
        outputs=[login_panel, main_panel, login_msg, session]
    )

    analyze_btn.click(
        fn=lambda s, u, f, sd, j, a, save: analyze_action(s, u, f, sd, j, a, save),
        inputs=[session, username_in, resume_file, set_default, job_desc, about_role, save_analysis],
        outputs=[home_status, home_score, home_missing, home_suggestions]
    )

def launch_ats():
    ats_app.launch(server_name="0.0.0.0", server_port=7861)
