"""
Routes:
    POST /upload       — accepts topics.txt, triggers batch run
    GET  /status       — SSE stream of per-topic progress events
    GET  /reports      — lists all .docx files with download links
    GET  /download/<f> — serves a report file
"""

import os
import json
import asyncio
import threading
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


if __name__ == "__main__":
    app.run(debug=True, port=5000)
