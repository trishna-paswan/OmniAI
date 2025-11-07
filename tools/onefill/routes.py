# tools/onefill/routes.py

from flask import Blueprint, render_template, request
from datetime import datetime
import subprocess
from fuzzywuzzy import fuzz
from .form_parser import extract_fields_from_form
from .autofiller import fill_google_form

# Ensure Playwright Chromium is ready
subprocess.run(["playwright", "install", "chromium"], check=False)

onefill_bp = Blueprint('onefill', __name__, template_folder='templates', static_folder='static')

submission_logs = []  # global list to track submission history


@onefill_bp.route("/")
def index():
    return render_template("onefill_index.html")


@onefill_bp.route("/dashboard")
def dashboard():
    return render_template(
        "onefill_dashboard.html",
        total_forms=len(submission_logs),
        total_fields=sum(log["fields_filled"] for log in submission_logs),
        success_rate=round(100 * sum(log["success"] for log in submission_logs) / len(submission_logs)) if submission_logs else 0,
        submission_logs=submission_logs
    )


@onefill_bp.route("/scan", methods=["POST"])
def scan():
    urls = [url.strip() for url in request.form["form_urls"].splitlines() if url.strip()]
    raw_fields = set()

    for url in urls:
        try:
            fields = extract_fields_from_form(url)
            raw_fields.update(fields)
        except Exception as e:
            print(f"❌ Failed to extract from {url}: {e}")

    normalization_map = {
        "full name": "name",
        "name": "name",
        "email address": "email",
        "phone number": "phone",
        "mobile number": "phone",
        "dob": "date of birth",
        "roll number": "roll number",
        "date of birth": "date of birth",
        "address": "address"
    }

    normalized_fields = set()
    for field in raw_fields:
        key = field.lower().strip()
        normalized_fields.add(normalization_map.get(key, field.strip()))

    # Fuzzy deduplication
    final_fields = []
    threshold = 80
    for new_field in sorted(normalized_fields):
        matched = False
        for i, existing in enumerate(final_fields):
            score = fuzz.token_sort_ratio(new_field.lower(), existing.lower())
            if score >= threshold:
                if len(new_field) < len(existing):
                    final_fields[i] = new_field
                matched = True
                break
        if not matched:
            final_fields.append(new_field)

    return render_template("onefill_unified_form.html", fields=sorted(final_fields), urls=urls)


@onefill_bp.route("/fill", methods=["POST"])
def fill():
    user_data = {k: v for k, v in request.form.items() if k != "urls"}
    urls = request.form.getlist("urls")
    results = []

    for url in urls:
        fields_filled = fill_google_form(url, user_data)
        success = fields_filled > 0
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

        submission_logs.append({
            "url": url,
            "fields_filled": fields_filled,
            "success": success,
            "timestamp": timestamp
        })

        results.append((url, fields_filled))

    return render_template("onefill_success.html", results=results)
