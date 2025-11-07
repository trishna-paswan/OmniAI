from flask import Flask, render_template
from tools.onefill.routes import onefill_bp
from tools.text_detector.routes import textdetector_bp
import threading, webbrowser
from flask import redirect
app = Flask(__name__)
app.register_blueprint(onefill_bp, url_prefix="/onefill")
app.register_blueprint(textdetector_bp, url_prefix="/text-detector")

@app.route("/")
def dashboard():
    return render_template("dashboard.html")

@app.route("/ats")
def ats_portal():
    from tools.ats_portal.ats_app import launch_ats
    threading.Thread(target=launch_ats, daemon=True).start()
    return redirect("http://127.0.0.1:7861")

if __name__ == "__main__":
    threading.Timer(1, lambda: webbrowser.open("http://127.0.0.1:5000")).start()
    app.run(debug=True)
