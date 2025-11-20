🌐 Omni_AI – Form Autofill • Resume Analyzer • Plagiarism Checker
<p align="center"> <img src="https://socialify.git.ci/trishna-paswan/OmniAI/image?font=Inter&language=1&name=1&owner=1&pattern=Floating%20Cogs&stargazers=1&theme=Dark" alt="Omni_AI Banner"/> </p> <p align="center"> Automated Google Form filling, smart resume analysis, and plagiarism checking — all combined into one powerful web-based toolkit. Omni_AI boosts productivity by automating repetitive tasks and offering AI-assisted insights for documents and academic work. </p> <p align="center"> <img src="https://img.shields.io/badge/Built%20With-Flask-blue.svg" /> <img src="https://img.shields.io/badge/Automation-Playwright-green.svg" /> <img src="https://img.shields.io/badge/Text%20Intelligence-FuzzyWuzzy-yellow.svg" /> <img src="https://img.shields.io/badge/PDF%20Processing-PyMuPDF-red.svg" /> <img src="https://img.shields.io/badge/Deployed%20On-Render-purple.svg" /> </p>
✅ 1. OneFill – Multi-Google Form AutoFiller

Extracts Google Form fields using Playwright

Uses Fuzzy Matching + Regex to correctly map labels

Generates a unified form for all required fields

Automatically fills & submits multiple forms

✅ 2. Resume Analyzer

Extracts text from PDF & DOCX resumes

Detects keywords, skills, ATS essentials

Generates ATS score + improvement recommendations

Helps optimize resumes for hiring systems

✅ 3. Plagiarism Checker

Detects content similarity using pattern & semantic matching

Highlights plagiarised text

Suggests clean, rephrased alternatives

Ensures academic integrity

🖥️ Demo
🌐 Live Link:
https://omniai-ud7z.onrender.com

🛠️ Tech Stack
Layer	Technology
Frontend	HTML5, Tailwind CSS, JavaScript
Backend	Python (Flask Framework)
Automation	Playwright
AI/Text Tools	FuzzyWuzzy, Regex
Document Processing	PyMuPDF, python-docx
Deployment	Render + Gunicorn

📁 Folder Structure
OmniAI/
 ┣ app.py
 ┣ templates/
 ┃ ┗ dashboard.html
 ┣ tools/
 ┃ ┣ ats_portal/
 ┃ ┃ ┗ ats_portal.py
 ┃ ┣ onefill/
 ┃ ┃ ┣ autofiller.py
 ┃ ┃ ┣ form_parser.py
 ┃ ┃ ┣ routes.py
 ┃ ┃ ┣ onefill_index.html
 ┃ ┃ ┣ onefill_unified_form.html
 ┃ ┃ ┗ onefill_success.html
 ┃ ┗ text_detector/
 ┃    ┣ textdetector_bp.py
 ┃    ┗ templates/
 ┃       ┗ text_detector.html
 ┗ requirements.txt

🧪 Local Setup
1. Clone the Repository
git clone https://github.com/trishna-paswan/OmniAI.git
cd OmniAI

2. Create a Virtual Environment
python3 -m venv .venv
source .venv/bin/activate

3. Install Requirements
pip install -r requirements.txt
playwright install chromium

4. Run the App
python app.py


Now visit:
👉 http://localhost:5000

✨ Author

Made with ❤️ by Trishna Kumari Paswan
