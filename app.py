from flask import Flask, render_template_string, request, jsonify
from teacher_slot_app.database import teachers_col  

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Teacher Free Slot Finder</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; margin: 40px; background-color: #f0f2f5; }
        .container { max-width: 500px; margin: auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
        h2 { color: #1a73e8; text-align: center; margin-bottom: 5px;}
        .university-name { text-align: center; color: #666; font-size: 0.9em; margin-bottom: 20px; }
        label { font-weight: bold; display: block; margin-top: 15px; }
        select, button { padding: 12px; margin: 8px 0; width: 100%; border: 1px solid #ddd; border-radius: 8px; font-size: 16px; }
        button { background-color: #1a73e8; color: white; cursor: pointer; border: none; font-weight: bold; }
        .error-msg { color: #d93025; background: #fce8e6; padding: 10px; border-radius: 4px; display: none; margin-bottom: 10px; border: 1px solid #fad2cf; }
        #results { margin-top: 25px; padding: 20px; background: #ffffff; border: 1px solid #e0e0e0; border-radius: 8px; display: none; }
        ul { list-style-type: none; padding: 0; }
        li { padding: 10px 0; border-bottom: 1px solid #eee; display: flex; align-items: center; }
        .badge { background: #e6f4ea; color: #1e8e3e; padding: 2px 8px; border-radius: 4px; font-size: 0.8em; margin-left: auto; }
    </style>
</head>
<body>
    <div class="container">
        <h2>Free Slot Finder</h2>
        <div class="university-name">Faculty Availability System</div>
        
        <div id="errorBox" class="error-msg"></div>
        
        <form id="searchForm">
            <label>Day:</label>
            <select id="day">
                <option value="MONDAY">Monday</option>
                <option value="TUESDAY">Tuesday</option>
                <option value="WEDNESDAY">Wednesday</option>
                <option value="THURSDAY">Thursday</option>
                <option value="FRIDAY">Friday</option>
            </select>

            <label>From (Start Time):</label>
            <select id="startTime">
                <option value="09:30">09:30 AM</option>
                <option value="10:20">10:20 AM</option>
                <option value="11:10">11:10 AM</option>
                <option value="12:00">12:00 PM</option>
                <option value="12:50">12:50 PM</option>
                <option value="13:05">01:05 PM (Lunch Ends)</option>
                <option value="13:55">01:55 PM</option>
                <option value="14:45">02:45 PM</option>
                <option value="15:35">03:35 PM</option>
            </select>

            <label>To (End Time):</label>
            <select id="endTime">
                <option value="10:20">10:20 AM</option>
                <option value="11:10">11:10 AM</option>
                <option value="12:00">12:00 PM</option>
                <option value="12:50">12:50 PM</option>
                <option value="13:55">01:55 PM</option>
                <option value="14:45">02:45 PM</option>
                <option value="15:35">03:35 PM</option>
                <option value="16:25">04:25 PM</option>
            </select>
            
            <button type="button" onclick="findTeachers()">Search Availability</button>
        </form>

        <div id="results">
            <strong>Available Faculty:</strong>
            <ul id="teacherList"></ul>
        </div>
    </div>

    <script>
        async function findTeachers() {
            const day = document.getElementById('day').value;
            const start = document.getElementById('startTime').value;
            const end = document.getElementById('endTime').value;
            const errorBox = document.getElementById('errorBox');
            const resultsDiv = document.getElementById('results');
            const list = document.getElementById('teacherList');

            // Logical Range Check
            if (start >= end) {
                errorBox.textContent = "⚠️ Invalid Range: Start time must be earlier than End time.";
                errorBox.style.display = "block";
                resultsDiv.style.display = "none";
                return;
            } else {
                errorBox.style.display = "none";
            }

            const response = await fetch(`/api/availability/free-teachers?day=${day}&start=${start}&end=${end}`);
            const data = await response.json();

            list.innerHTML = "";
            if (data.length > 0) {
                data.forEach(t => {
                    const li = document.createElement('li');
                    li.innerHTML = `<span>👤 ${t.name}</span> <span class="badge">Available</span>`;
                    list.appendChild(li);
                });
            } else {
                list.innerHTML = "<li>No faculty available for this range.</li>";
            }
            resultsDiv.style.display = "block";
        }
    </script>
</body>
</html>
"""

# Route define kiya jisse free teachers ko fetch kare
@app.route('/api/availability/free-teachers', methods=['GET'])
def get_free_teachers():
    day = request.args.get('day', '').upper()
    start = request.args.get('start', '')
    end = request.args.get('end', '')

    # MongoDB Query to find free teachers in the specified time range
    query = {
        "busy_slots": {
            "$not": {
                "$elemMatch": {
                    "day": day,
                    "time": {"$regex": f"({start}|{end})"}
                }
            }
        }
    }
    
    free_teachers = list(teachers_col.find(query, {"_id": 0, "name": 1}))
    return jsonify(free_teachers)

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

if __name__ == '__main__':
    app.run(debug=True, port=8080)