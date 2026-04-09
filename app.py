"""
Routes:
    POST /upload          — accepts topics.txt, triggers batch run
    GET  /status          — SSE stream of per-topic progress events
    GET  /reports         — lists all .docx files with download links
    GET  /download/<f>    — serves a report file
    POST /save-key        — save API key to .env
    POST /save-config     — save agent config to .env
    GET  /get-settings    — return current settings
    POST /clear-reports   — delete all .docx files
"""

import os
import json
import asyncio
import threading
import glob
from flask import Flask, request, jsonify, Response, render_template, send_from_directory
from batch import run_batch, read_topics, save_batch_summary, sse_queue

app = Flask(__name__)
REPORTS_DIR = "reports"


def run_batch_in_thread(topics: list[str]):
    """Run async batch in a background thread."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    results = loop.run_until_complete(run_batch(topics))
    if results:
        save_batch_summary(results)
    loop.close()
    sse_queue.put({"event": "batch_complete", "topic": "", "data": {"total": len(results)}})


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400
    file = request.files["file"]
    if not file.filename.endswith(".txt"):
        return jsonify({"error": "Only .txt files accepted"}), 400

    content = file.read().decode("utf-8")
    topics = [line.strip() for line in content.splitlines() if line.strip()]

    if not topics:
        return jsonify({"error": "No topics found in file"}), 400

    thread = threading.Thread(target=run_batch_in_thread, args=(topics,))
    thread.daemon = True
    thread.start()

    return jsonify({"message": f"Batch started for {len(topics)} topics", "topics": topics})


@app.route("/status")
def status():
    """SSE endpoint — streams topic events to the browser."""
    def stream():
        while True:
            event = sse_queue.get()
            data = json.dumps(event)
            yield f"data: {data}\n\n"
            if event.get("event") == "batch_complete":
                break

    return Response(stream(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.route("/reports")
def reports():
    """Return list of all .docx reports."""
    os.makedirs(REPORTS_DIR, exist_ok=True)
    files = [f for f in os.listdir(REPORTS_DIR) if f.endswith(".docx")]
    files.sort(reverse=True)
    return jsonify({"reports": files})


@app.route("/download/<filename>")
def download(filename):
    return send_from_directory(REPORTS_DIR, filename, as_attachment=True)


@app.route("/preview/<filename>")
def preview(filename):
    """Return .docx content as plain text for preview."""
    try:
        from docx import Document
        path = os.path.join(REPORTS_DIR, filename)
        doc = Document(path)
        content = "\n\n".join([p.text for p in doc.paragraphs if p.text.strip()])
        return jsonify({"filename": filename, "content": content})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/save-key", methods=["POST"])
def save_key():
    """Save an API key to the .env file."""
    data = request.get_json()
    provider = data.get("provider", "").lower()
    key = data.get("key", "").strip()

    if provider not in ("anthropic", "tavily"):
        return jsonify({"error": "Unknown provider"}), 400
    if not key:
        return jsonify({"error": "Key cannot be empty"}), 400

    env_var = "ANTHROPIC_API_KEY" if provider == "anthropic" else "TAVILY_API_KEY"

    # Validate key format
    if provider == "anthropic" and not key.startswith("sk-ant-"):
        return jsonify({"error": "Anthropic key should start with sk-ant-"}), 400
    if provider == "tavily" and not key.startswith("tvly-"):
        return jsonify({"error": "Tavily key should start with tvly-"}), 400

    _write_env_var(env_var, key)
    os.environ[env_var] = key
    return jsonify({"message": "Key saved"})


@app.route("/save-config", methods=["POST"])
def save_config():
    """Save agent configuration to .env."""
    data = request.get_json()
    _write_env_var("MAX_SUBQUERIES", str(data.get("max_subqueries", 3)))
    _write_env_var("MAX_ITERATIONS", str(data.get("max_iterations", 10)))
    _write_env_var("MAX_CONCURRENT", str(data.get("max_concurrent", 10)))
    return jsonify({"message": "Config saved"})


@app.route("/get-settings")
def get_settings():
    """Return current settings and whether API keys exist."""
    from dotenv import load_dotenv
    load_dotenv(override=True)
    return jsonify({
        "has_anthropic": bool(os.environ.get("ANTHROPIC_API_KEY")),
        "has_tavily": bool(os.environ.get("TAVILY_API_KEY")),
        "max_subqueries": int(os.environ.get("MAX_SUBQUERIES", 3)),
        "max_iterations": int(os.environ.get("MAX_ITERATIONS", 10)),
        "max_concurrent": int(os.environ.get("MAX_CONCURRENT", 10)),
    })


@app.route("/clear-reports", methods=["POST"])
def clear_reports():
    """Delete all .docx files from the reports directory."""
    os.makedirs(REPORTS_DIR, exist_ok=True)
    files = glob.glob(os.path.join(REPORTS_DIR, "*.docx"))
    for f in files:
        os.remove(f)
    return jsonify({"message": f"Deleted {len(files)} report(s)"})


def _write_env_var(key: str, value: str):
    """Write or update a key=value pair in the .env file."""
    env_path = ".env"
    lines = []
    found = False

    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

    for i, line in enumerate(lines):
        if line.startswith(key + "="):
            lines[i] = f"{key}={value}\n"
            found = True
            break

    if not found:
        lines.append(f"{key}={value}\n")

    with open(env_path, "w", encoding="utf-8") as f:
        f.writelines(lines)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
