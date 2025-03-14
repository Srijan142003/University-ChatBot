import os
import pdfkit
from core_functions.leave_requests import process_student_leave_request, process_teacher_leave_request
from core_functions.academic_queries import query_backlog_exam_details, query_academic_calendar
from flask_cors import CORS
from flask import Flask, request, render_template, jsonify, send_from_directory, redirect, url_for, session, make_response
from pymongo import MongoClient
import logging
from datetime import datetime
from typing import Dict

app = Flask(__name__)
app.secret_key = '12345678'  # Replace with a random secret key

# Enable CORS for all routes
CORS(app)

# Configure Logging
logging.basicConfig(level=logging.INFO)

# MongoDB Connection
MONGO_URI = os.environ.get('MONGO_URI', "mongodb+srv://srijankundu14:tLH9raY57j3bQH9k@cluster1.xdb31.mongodb.net/University_Data_Center")
client = MongoClient(MONGO_URI)
db = client["University_Data_Center"]
student_collection = db["student"]
teacher_collection = db["teachers"]

# Ensure "certificates" folder exists
CERTIFICATES_DIR = "certificates"
if not os.path.exists(CERTIFICATES_DIR):
    os.makedirs(CERTIFICATES_DIR)

@app.after_request
def add_security_headers(response):
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data: https://i.ibb.co; "
        "connect-src 'self';"
    )
    return response

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        logging.info(f"Attempting login with email: {email}")
        
        # Check in student collection
        user = student_collection.find_one({"email": email, "password": password})
        if user:
            session['user_id'] = user['user_id']
            session['user_name'] = user['name']
            session['role'] = 'student'
            session['logged_in'] = True
            logging.info(f"Student login successful for user_id: {user['user_id']}")
            return redirect(url_for('chatbot'))
        
        # Check in teacher collection
        user = teacher_collection.find_one({"email": email, "password": password})
        if user:
            session['user_id'] = user['user_id']
            session['user_name'] = user['name']
            session['role'] = 'teacher'
            session['logged_in'] = True
            logging.info(f"Teacher login successful for user_id: {user['user_id']}")
            return redirect(url_for('chatbot'))
        
        logging.warning("Invalid credentials")
        return "Invalid credentials", 401
    
    return render_template('login.html')

@app.route('/chatbot')
def chatbot():
    if 'logged_in' in session and session['logged_in']:
        return render_template('univ_bot.html')
    else:
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# Route to Generate Certificate
@app.route('/generate_certificate', methods=['POST'])
def generate_certificate() -> str:
    try:
        # Ensure request contains JSON data
        if not request.is_json:
            return jsonify({"error": "Invalid request format. Expected JSON."}), 400
        
        data: Dict = request.json
        user_id = session.get("user_id")
        certificate_type = data.get("certificate_type")
        
        if not user_id:
            return jsonify({"error": "User not logged in"}), 400
        if not certificate_type:
            return jsonify({"error": "Missing certificate_type field"}), 400
        
        # Determine collection based on user_id prefix
        if user_id.startswith("STU"):
            collection = student_collection
            role = "student"
        elif user_id.startswith("TCH"):
            collection = teacher_collection
            role = "teacher"
        else:
            return jsonify({"error": "Invalid user_id"}), 400
        
        # Find user by user_id
        user = collection.find_one({"user_id": user_id})
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        # Remove MongoDB ObjectId and unnecessary fields
        user.pop("_id", None)
        user.pop("password", None)
        
        # Get current date
        current_date = datetime.now().strftime("%d-%m-%Y")
        
        # Generate HTML content based on certificate type and role
        if role == "student":
            if certificate_type.lower() == "bonafide":
                html_content = render_template('student_bonafide.html', student=user, current_date=current_date)
                filename = f"{user.get('name', 'Unknown')}_Bonafide_Certificate.pdf"
            elif certificate_type.lower() == "noc":
                html_content = render_template('student_noc.html', student=user, current_date=current_date)
                filename = f"{user.get('name', 'Unknown')}_NOC_Certificate.pdf"
            else:
                return jsonify({"error": "Invalid certificate type"}), 400
        elif role == "teacher":
            if certificate_type.lower() == "bonafide":
                html_content = render_template('teacher_bonafide.html', teacher=user, current_date=current_date)
                filename = f"{user.get('name', 'Unknown')}_Teacher_Bonafide_Certificate.pdf"
            elif certificate_type.lower() == "noc":
                html_content = render_template('teacher_noc.html', teacher=user, current_date=current_date)
                filename = f"{user.get('name', 'Unknown')}_Teacher_NOC_Certificate.pdf"
            else:
                return jsonify({"error": "Invalid certificate type"}), 400
        
        # Generate Safe Filename
        safe_name = "".join(c if c.isalnum() or c in " _-" else "_" for c in user.get('name', 'Unknown'))
        file_path = os.path.join(CERTIFICATES_DIR, filename)
        
        # Ensure wkhtmltopdf path is correct (Modify if needed)
        wkhtmltopdf_path = os.environ.get('WKHTMLTOPDF_PATH', "C:/Program Files/wkhtmltopdf/bin/wkhtmltopdf.exe")
        config = pdfkit.configuration(wkhtmltopdf=wkhtmltopdf_path)
        pdfkit.from_string(html_content, file_path, configuration=config)
        
        logging.info(f"Certificate generated: {filename}")
        
        # Return a Clickable Download Link
        return f"""
        <a href="/download_certificate?filename={filename}">Download {certificate_type.capitalize()} Certificate</a>
        """
    
    except Exception as e:
        logging.error(f"Error generating certificate: {e}")
        return jsonify({"error": str(e)}), 500

# Route to Download Certificate
@app.route('/download_certificate', methods=['GET'])
def download_certificate():
    filename = request.args.get('filename')
    if filename:
        return send_from_directory(CERTIFICATES_DIR, filename, as_attachment=True)
    else:
        return jsonify({"error": "Missing filename"}), 400

@app.route('/leave-request', methods=['POST'])
def handle_leave_request():
    try:
        data = request.json
        user_id = data.get('user_id')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        cause = data.get('cause')
        leave_type = data.get('leave_type')

        if not user_id or not start_date or not end_date or not cause or not leave_type:
            return jsonify({"message": "Missing required fields in the request."}), 400

        if user_id.startswith('STU'):
            response = process_student_leave_request(user_id, start_date, end_date, cause, leave_type)
        elif user_id.startswith('TCH'):
            response = process_teacher_leave_request(user_id, start_date, end_date, cause, leave_type)
        else:
            return jsonify({"message": "Invalid user ID. Use 'STU' for students or 'TCH' for teachers."}), 400

        return jsonify({"message": response})
    except Exception as e:
        logging.error(f"Error handling leave request: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/query", methods=["POST"])
def query():
    try:
        data = request.get_json()
        if not data or "query" not in data:
            return jsonify({"response": "Invalid request! Please provide a valid query."}), 400
        
        user_input = data["query"].lower()
        course_code, batch_year, event_type, semester = None, None, None, None
        
        words = user_input.split()
        for word in words:
            if word.startswith(("cs", "ee", "me", "ce", "ch")):
                course_code = word.upper()
            elif word.isdigit() and len(word) == 4:
                batch_year = int(word)
            elif word in ["exam", "holiday", "lecture"]:
                event_type = word.capitalize()
            elif word in ["spring", "fall"]:
                semester = word.capitalize()
        
        if course_code or batch_year:
            results = query_backlog_exam_details(course_code=course_code, batch_year=batch_year)
            if results:
                response_text = "📅 Backlog Exam Details:\n" + "\n".join(
                    f"- **Course Code:** {exam['course_code']}, **Course Name:** {exam['course_name']}\n"
                    f"  **Date:** {exam['exam_date']}, **Time:** {exam['exam_time']}, **Location:** {exam['exam_location']}"
                    for exam in results
                )
                return jsonify({"response": response_text})
            else:
                return jsonify({"response": "No backlog exams found for the given criteria."})

        elif event_type or semester:
            results = query_academic_calendar(event_type=event_type, semester=semester)
            if results:
                response_text = (
                    "<table style='border-collapse: collapse; width: 100%; text-align: center;'>"
                    "<tr style='border-bottom: 1px solid #ddd;'><th style='padding: 8px;'>Event Name</th>"
                    "<th style='padding: 8px;'>Start Date</th><th style='padding: 8px;'>End Date</th>"
                    "<th style='padding: 8px;'>Description</th></tr>"
                )
                for event in results:
                    start_date_formatted = datetime.strptime(event['start_date'], "%Y-%m-%d").strftime("%d-%m-%Y")
                    end_date_formatted = datetime.strptime(event['end_date'], "%Y-%m-%d").strftime("%d-%m-%Y")
                    response_text += (
                        f"<tr style='border-bottom: 1px solid #ddd;'><td style='padding: 8px;'>{event['event_name']}</td>"
                        f"<td style='padding: 8px;'>{start_date_formatted}</td>"
                        f"<td style='padding: 8px;'>{end_date_formatted}</td>"
                        f"<td style='padding: 8px;'>{event['description']}</td></tr>"
                    )
                response_text += "</table>"
                return jsonify({"response": response_text})
            else:
                return jsonify({"response": "No academic calendar events found for the given criteria."})

        return jsonify({"response": "I couldn't understand your query. Please ask about a course code, batch year, event type, or semester."})
    except Exception as e:
        logging.error(f"Error processing query: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)