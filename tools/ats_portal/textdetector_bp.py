from flask import Blueprint, render_template, request
import re
import math
import docx2txt
from PyPDF2 import PdfReader
from collections import Counter
import os

textdetector_bp = Blueprint("textdetector", __name__, template_folder="templates", static_folder="static")

# --- Extract text from uploaded file ---
def extract_text(filepath):
    if filepath.endswith(".txt"):
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    elif filepath.endswith(".docx"):
        return docx2txt.process(filepath)
    elif filepath.endswith(".pdf"):
        reader = PdfReader(filepath)
        return " ".join(page.extract_text() or "" for page in reader.pages)
    else:
        raise ValueError("Unsupported file type! Please upload .txt, .docx, or .pdf")

# --- Sentence splitting helper ---
def split_sentences(text):
    return [s.strip() for s in re.split(r'(?<=[.!?])\s+|\n+', text) if s.strip()]

# --- Heuristic AI-likelihood scoring ---
def ai_likelihood_score(text):
    sentences = split_sentences(text)
    if not sentences:
        return 0.0

    lengths = [len(s.split()) for s in sentences if s.strip()]
    avg_len = sum(lengths) / len(lengths)
    std_len = (sum((l - avg_len) ** 2 for l in lengths) / len(lengths)) ** 0.5
    length_uniformity = 1 - (std_len / avg_len) if avg_len > 0 else 0

    words = re.findall(r"\b\w+\b", text.lower())
    total_words = len(words)
    unique_words = len(set(words))
    diversity = unique_words / total_words if total_words > 0 else 0

    rare_words = [w for w, c in Counter(words).items() if c == 1]
    rare_ratio = len(rare_words) / total_words if total_words > 0 else 0

    score = (length_uniformity * 0.4 + (1 - diversity) * 0.4 + (0.3 - rare_ratio) * 1.5)
    score = max(0, min(score, 1))
    return round(score * 100, 2)

# --- Flask route ---
@textdetector_bp.route("/", methods=["GET", "POST"])
def home():
    result = None
    explanation = None
    filename = None

    if request.method == "POST":
        uploaded = request.files.get("file")
        if uploaded:
            filename = uploaded.filename
            filepath = os.path.join("uploads", filename)
            os.makedirs("uploads", exist_ok=True)
            uploaded.save(filepath)

            text = extract_text(filepath)
            score = ai_likelihood_score(text)

            # --- Determine category ---
            if score >= 90:
                result = f"🚨 {score}% very likely AI-generated"
                explanation = "The text strongly matches AI writing patterns — phrasing, structure, and vocabulary are highly machine-like."
            elif 80 <= score < 90:
                result = f"⚠️ {score}% likely AI-generated"
                explanation = "The content shows many signs of AI generation, though a small human touch might be present."
            elif 63 <= score < 80:
                result = f"🟠 {score}% possibly AI-generated"
                explanation = "This range often indicates a mix — AI assistance with human edits or prompts."
            elif 45 <= score < 63:
                result = f"🟡 {score}% somewhat AI-influenced"
                explanation = "The text has some AI-like traits (smooth flow, generic tone) but overall feels human-influenced."
            else:
                result = f"✅ Only {score}% AI-likelihood detected"
                explanation = f"The text is {100 - score}% likely human-written — with natural variation and authenticity."

    return render_template("text_detector.html", result=result, explanation=explanation, filename=filename)
