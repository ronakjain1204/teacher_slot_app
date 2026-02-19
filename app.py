import os
import threading
from flask import Flask, render_template_string, request, jsonify
from werkzeug.utils import secure_filename
from database import teachers_col
from parser import run_ai_parser
from flask_cors import CORS 

app = Flask(__name__)
CORS(app) # Fixed: Correct placement

app.config['UPLOAD_FOLDER'] = 'data'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>AI-Nexus Faculty Finder</title>
    <style>
        body { font-family: sans-serif; background: #f0f2f5; padding: 40px; }
        .card { background: white; padding: 25px; border-radius: 12px; max-width: 500px; margin: auto; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
        input, select, button { width: 100%; padding: 10px; margin: 10px 0; border-radius: 5px; border: 1px solid #ddd; }
        button { background: #1a73e8; color: white; border: none; font-weight: bold; cursor: pointer; }
        .upload-area { border: 2px dashed #1a73e8; padding: 15px; background: #f8faff; margin-top: 20px; }
    </style>
</head>
<body>
    <div class="card">
        <h2>Faculty Finder</h2>
        <select id="day">
            <option value="MONDAY">Monday</option>
            <option value="TUESDAY">Tuesday</option>
            <option value="WEDNESDAY">Wednesday</option>
            <option value="THURSDAY">Thursday</option>
            <option value="FRIDAY">Friday</option>
            <option value="SATURDAY">Saturday</option>
        </select>
        <input type="text" id="time" placeholder="Time (e.g., 09:30)">
        <button onclick="search()">Search Available Faculty</button>
        <div id="results"></div>

        <div class="upload-area">
            <h4>Update Timetable (PDF)</h4>
            <input type="file" id="pdfFile">
            <button style="background:#6c757d" onclick="upload()">Upload & Sync</button>
            <p id="status" style="font-size: 0.8em;"></p>
        </div>
    </div>

    <script>
        async function search() {
            const day = document.getElementById('day').value;
            const time = document.getElementById('time').value;
            // FIXED: Using relative path for the website itself
            const res = await fetch(`/api/free?day=${day}&time=${time}`);
            const data = await res.json();
            document.getElementById('results').innerHTML = data.map(t => `<div>✅ ${t.name}</div>`).join('');
        }

        async function upload() {
            const file = document.getElementById('pdfFile').files[0];
            const status = document.getElementById('status');
            if(!file) return alert("Select a file");
            const fd = new FormData(); fd.append('file', file);
            status.textContent = "Processing... this may take a few minutes.";
            const res = await fetch('/api/upload', { method: 'POST', body: fd });
            const data = await res.json();
            status.textContent = data.message || data.error;
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index(): return render_template_string(HTML_TEMPLATE)

@app.route('/api/free')
def get_free():
    day = request.args.get('day', 'MONDAY').upper()
    time = request.args.get('time', '')
    # This query finds teachers who DO NOT have a busy slot at this day/time
    query = {"busy_slots": {"$not": {"$elemMatch": {"day": day, "time": {"$regex": time}}}}}
    return jsonify(list(teachers_col.find(query, {"_id": 0, "name": 1})))

@app.route('/api/upload', methods=['POST'])
def upload_file():
    file = request.files.get('file')
    if file and file.filename.endswith('.pdf'):
        filename = secure_filename(file.filename)
        path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(path)
        threading.Thread(target=run_ai_parser, args=(path,)).start()
        return jsonify({"message": "Upload started in background."})
    return jsonify({"error": "Invalid file"}), 400

if __name__ == '__main__':
    # Use port 8080 for Render compatibility
    app.run(host='0.0.0.0', port=8080)