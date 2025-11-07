from flask import Flask, render_template
from tools.onefill.routes import onefill_bp
from tools.text_detector.routes import textdetector_bp
import threading
import webbrowser

# Flask app
app = Flask(__name__)

# Register Blueprints (Flask tools)
app.register_blueprint(onefill_bp, url_prefix="/onefill")
app.register_blueprint(textdetector_bp, url_prefix="/text-detector")

# Route for Gradio ATS Portal
@app.route("/ats")
def ats_portal():
    # Run Gradio app in a new thread so Flask doesn’t block
    def run_gradio():
        from tools.ats_portal.ats_app import launch_gradio
        launch_gradio()
    threading.Thread(target=run_gradio, daemon=True).start()
    return render_template("launch_gradio.html")

@app.route("/")
def dashboard():
    return render_template("dashboard.html")

if __name__ == "__main__":
    print("🚀 Opening dashboard at http://127.0.0.1:5000")
    threading.Timer(1, lambda: webbrowser.open("http://127.0.0.1:5000")).start()
    app.run(debug=True)
