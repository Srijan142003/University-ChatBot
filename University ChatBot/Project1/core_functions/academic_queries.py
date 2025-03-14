from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os

app = Flask(__name__)
CORS(app)

# 🔹 Load JSON Files into Lists of Dictionaries
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
backlog_exam_details_path = os.path.join(BASE_DIR, "data/University_Data_Center.Backlog-Exam-Details.json")
academic_calendar_path = os.path.join(BASE_DIR, "data/University_Data_Center.Academic-Calander.json")

try:
    with open(backlog_exam_details_path, 'r') as file:
        backlog_exam_details = json.load(file)
    with open(academic_calendar_path, 'r') as file:
        academic_calendar = json.load(file)
except FileNotFoundError as e:
    print(f"Error: {e}")
    backlog_exam_details = []
    academic_calendar = []

# 🔹 Helper Function: Query Backlog Exam Details
def query_backlog_exam_details(course_code=None, batch_year=None):
    results = backlog_exam_details

    if course_code:
        results = [exam for exam in results if exam['course_code'] == course_code]
    if batch_year:
        results = [exam for exam in results if str(batch_year) in exam['eligible_batches']]

    return results

# 🔹 Helper Function: Query Academic Calendar
def query_academic_calendar(event_type=None, semester=None):
    results = academic_calendar

    if event_type:
        results = [event for event in results if event['event_type'].lower() == event_type.lower()]
    if semester:
        results = [event for event in results if event['semester'].lower() == semester.lower()]

    return results

@app.route("/query", methods=["POST"])
def query():
    data = request.get_json()
    if not data or "query" not in data:
        return jsonify({"response": "Invalid request! Please provide a valid query."})

    user_input = data["query"].lower()
    course_code = None
    batch_year = None
    event_type = None
    semester = None

    # 🔹 Parse User Input
    words = user_input.split()
    for word in words:
        if word.startswith(("cs", "ee", "me", "ce", "ch")):  # Detect course codes like CS101, EE201
            course_code = word.upper()
        elif word.isdigit() and len(word) == 4:  # Detect batch year like 2020
            batch_year = int(word)
        elif word in ["exam", "holiday", "lecture"]:  # Detect event types like Exam or Holiday
            event_type = word.capitalize()
        elif word in ["spring", "fall"]:  # Detect semester like Spring or Fall
            semester = word.capitalize()

    # 🔹 Query Backlog Exam Details
    if course_code or batch_year:
        results = query_backlog_exam_details(course_code=course_code, batch_year=batch_year)
        if results:
            response_text = f"📅 Backlog Exam Details:\n"
            for exam in results:
                response_text += (
                    f"- **Course Code:** {exam['course_code']}, **Course Name:** {exam['course_name']}\n"
                    f"  **Date:** {exam['exam_date']}, **Time:** {exam['exam_time']}, **Location:** {exam['exam_location']}\n"
                )
            return jsonify({"response": response_text})
        else:
            return jsonify({"response": "No backlog exams found for the given criteria."})

    # 🔹 Query Academic Calendar
    elif event_type or semester:
        results = query_academic_calendar(event_type=event_type, semester=semester)
        if results:
            response_text = f"📅 Academic Calendar Events:\n"
            for event in results:
                response_text += (
                    f"- **Event Name:** {event['event_name']}, **Start Date:** {event['start_date']}, "
                    f"**End Date:** {event['end_date']}, **Description:** {event['description']}\n"
                )
            return jsonify({"response": response_text})
        else:
            return jsonify({"response": "No academic calendar events found for the given criteria."})

    return jsonify({"response": "I couldn't understand your query. Please ask about a course code, batch year, event type, or semester."})

if __name__ == "__main__":
    app.run(debug=True)
