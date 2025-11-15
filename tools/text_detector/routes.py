from flask import Blueprint, render_template, request
import re
import docx2txt
from PyPDF2 import PdfReader
from collections import Counter
import os

textdetector_bp = Blueprint(
    "textdetector",
    __name__,
    template_folder="templates",
    static_folder="static"
)

# Extract text from uploaded file
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
        raise ValueError("Unsupported file type! Please upload .txt, .docx, or .pdf.")

# Split text into sentences
def split_sentences(text):
    return [s.strip() for s in re.split(r'(?<=[.!?])\s+|\n+', text) if s.strip()]


# AI-likelihood score (heuristic model)
def ai_likelihood_score(text):
    sentences = split_sentences(text)
    if not sentences:
        return 0.0

    lengths = [len(s.split()) for s in sentences if s.strip()]
    avg_len = sum(lengths) / len(lengths)
    std_len = (sum((l - avg_len) ** 2 for l in lengths) / len(lengths)) ** 0.5
    length_uniformity = 1 - (std_len / avg_len) if avg_len else 0

    words = re.findall(r"\b\w+\b", text.lower())
    total_words = len(words)
    unique_words = len(set(words))
    diversity = unique_words / total_words if total_words else 0

    rare_words = [w for w, c in Counter(words).items() if c == 1]
    rare_ratio = len(rare_words) / total_words if total_words else 0

    score = (length_uniformity * 0.4 + (1 - diversity) * 0.4 + (0.3 - rare_ratio) * 1.5)
    score = max(0, min(score, 1))
    return round(score * 100, 2)


# Flask Page Route
@textdetector_bp.route("/", methods=["GET", "POST"])
def home():
    result = None
    explanation = None
    filename = None

    if request.method == "POST":
        uploaded = request.files.get("file")

        if uploaded:
            filename = uploaded.filename
            os.makedirs("uploads", exist_ok=True)
            filepath = os.path.join("uploads", filename)
            uploaded.save(filepath)

            text = extract_text(filepath)
            score = ai_likelihood_score(text)

            # Score category
            if score >= 90:
                result = f"🚨 {score}% Very Likely AI-Generated"
                explanation = "Highly machine-like patterns and uniformity."
            elif score >= 80:
                result = f"⚠️ {score}% Likely AI-Generated"
                explanation = "Multiple AI traits detected."
            elif score >= 63:
                result = f"🟠 {score}% Possibly AI-Generated"
                explanation = "Could be AI-assisted or mixed writing."
            elif score >= 45:
                result = f"🟡 {score}% Somewhat AI-Influenced"
                explanation = "Shows some AI-like flow but still human-like."
            else:
                result = f"✅ Only {score}% AI-likelihood detected"
                explanation = f"Mostly human-written ({100 - score}% human score)."

    return render_template(
        "text_detector.html",
        result=result,
        explanation=explanation,
        filename=filename
    )
