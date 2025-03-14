from flask import Flask, request, render_template, jsonify, send_from_directory
from pymongo import MongoClient
import pdfkit
import os
import logging
from datetime import datetime
from typing import Dict

app = Flask(__name__)

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

# Route to Generate Certificate
@app.route('/generate_certificate', methods=['POST'])
def generate_certificate() -> str:
    try:
        # Ensure request contains JSON data
        if not request.is_json:
            return jsonify({"error": "Invalid request format. Expected JSON."}), 400
        
        data: Dict = request.json
        user_id = data.get("user_id")
        certificate_type = data.get("certificate_type")
        
        if not user_id:
            return jsonify({"error": "Missing user_id field"}), 400
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
        return jsonify({"error": str(e)}), 500

# Route to Download Certificate
@app.route('/download_certificate', methods=['GET'])
def download_certificate():
    filename = request.args.get('filename')
    if filename:
        return send_from_directory(CERTIFICATES_DIR, filename, as_attachment=True)
    else:
        return jsonify({"error": "Missing filename"}), 400

if __name__ == "__main__":
    app.run(debug=True)
