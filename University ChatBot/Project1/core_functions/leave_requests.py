from pymongo import MongoClient
import requests
import os
from flask import Flask, request, jsonify
from datetime import datetime

# Connect to MongoDB
client = MongoClient('mongodb+srv://srijankundu14:password@cluster1.xdb31.mongodb.net/')
db = client['University_Data_Center']
students_collection = db['student']
teachers_collection = db['teachers']

# Check connection
print("Connected to MongoDB and database 'University_Data_Center'")

def get_student_attendance(user_id):
    student = students_collection.find_one({"user_id": user_id})
    if student:
        return student.get("attendance_percentage", None)
    else:
        return None

def get_teacher_leave_credits(user_id):
    teacher = teachers_collection.find_one({"user_id": user_id})
    if teacher:
        return teacher.get("leave_credits", None)
    else:
        return None

def process_student_leave_request(user_id: str, start_date: str, end_date: str, cause: str, leave_type: str) -> str:
    attendance = get_student_attendance(user_id)
    if attendance is None:
        return "User not found. Please check the user ID."
    
    if attendance < 70:
        return "Your leave request cannot be auto-approved due to low attendance. Please contact the administrators."
    
    # Convert date format to DD-MM-YYYY
    start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
    end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
    start_date_formatted = start_date_obj.strftime("%d-%m-%Y")
    end_date_formatted = end_date_obj.strftime("%d-%m-%Y")
    duration = (end_date_obj - start_date_obj).days + 1
    
    if duration > 7:
        return "Your leave request cannot be auto-approved due to excessive duration. Please contact the administrators."
    
    # Generate approval message if criteria are met
    approval_message = f"Student ID: {user_id} has been granted leave from {start_date_formatted} to {end_date_formatted} due to {cause}."
    return approval_message

def process_teacher_leave_request(user_id: str, start_date: str, end_date: str, cause: str, leave_type: str) -> str:
    leave_credits = get_teacher_leave_credits(user_id)
    if leave_credits is None:
        return "Teacher not found. Please check the user ID."
    
    # Convert date format to DD-MM-YYYY
    start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
    end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
    start_date_formatted = start_date_obj.strftime("%d-%m-%Y")
    end_date_formatted = end_date_obj.strftime("%d-%m-%Y")
    duration = (end_date_obj - start_date_obj).days + 1
    
    if duration > leave_credits:
        return "Your leave request cannot be approved due to insufficient leave credits."
    
    # Update leave credits
    teachers_collection.update_one({"user_id": user_id}, {"$inc": {"leave_credits": -duration}})
    remaining_credits = leave_credits - duration
    
    # Generate approval message if criteria are met
    approval_message = f"Teacher with User ID: {user_id} has been granted leave from {start_date_formatted} to {end_date_formatted} due to {cause}. Remaining leave credits: {remaining_credits}."
    return approval_message

def process_student_leave_request_with_gpt(user_id, purpose, duration):
    attendance = get_student_attendance(user_id)
    if attendance is None:
        return "User not found. Please check the user ID."
    
    if duration > 7 or attendance < 60:
        return "Your leave request cannot be auto-approved. Please contact the administrators."
    else:
        api_key = os.environ.get('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')
        url = "https://api-inference.huggingface.co/models/gpt2"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "inputs": f"Student ID: {user_id} has {attendance}% attendance. Generate leave approval message for {duration} days.",
            "max_length": 50,
            "num_return_sequences": 1
        }
        try:
            response = requests.post(url, headers=headers, json=data)
            if response.status_code == 200:
                approval_message = response.json()[0]['generated_text']
                return approval_message
            else:
                return f"Failed to generate approval message. Error: {response.status_code}, {response.text}"
        except Exception as e:
            return f"An error occurred: {str(e)}"

app = Flask(__name__)

@app.route('/leave-request', methods=['POST'])
def handle_leave_request():
    data = request.json
    user_id = data['user_id']
    
    if user_id.startswith('STU'):
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        cause = data.get('cause')
        leave_type = data.get('leave_type')
        
        if start_date and end_date and cause and leave_type:
            response = process_student_leave_request(user_id, start_date, end_date, cause, leave_type)
        else:
            purpose = data.get('purpose')
            duration = data.get('duration')
            
            if purpose and duration:
                response = process_student_leave_request_with_gpt(user_id, purpose, int(duration))
            else:
                return jsonify({"message": "Missing required fields in the request."})
    elif user_id.startswith('TCH'):
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        cause = data.get('cause')
        leave_type = data.get('leave_type')
        
        if start_date and end_date and cause and leave_type:
            response = process_teacher_leave_request(user_id, start_date, end_date, cause, leave_type)
        else:
            return jsonify({"message": "Missing required fields in the request."})
    else:
        response = "Invalid user ID. Please ensure it starts with 'STU' for students or 'TCH' for teachers."
    
    return jsonify({"message": response})

if __name__ == '__main__':
    app.run(debug=True)
