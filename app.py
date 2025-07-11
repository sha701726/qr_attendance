# app.py
from Backup import export_to_google_sheet as backup
from models import UserRegister, AttendanceAction, CheckStatusRequest
from flask import Flask, request, jsonify, render_template
from database import get_connection
from oauth2client.service_account import ServiceAccountCredentials
from flask_cors import CORS
from datetime import datetime, date
from supabase import create_client
from dotenv import load_dotenv
import pytz
import gspread
import os

load_dotenv()
supabase = get_connection()
ist = pytz.timezone('Asia/Kolkata')
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

app = Flask(__name__)
CORS(app, supports_credentials=True, resources={r"/api/*": {"origins": "https://qr-attendance-sy8f.onrender.com"}})


@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/register", methods=["POST"])
def register_user():
    try:
        data = request.json
        user = UserRegister(**data)

        print("Registration request:", data)

        # Step 1: Check if user already exists
        existing_user = supabase.table("employees") \
            .select("*") \
            .eq("employee_id", user.employeeId) \
            .eq("mobile_no", user.mobile) \
            .execute()

        if existing_user.data:
            user_data = existing_user.data[0]
            return jsonify({
                "user_id": user_data["id"],
                "message": "User already registered",
                "user_data": {
                    "fullName": user_data["full_name"],
                    "mobile": user_data["mobile_no"],
                    "employeeId": user_data["employee_id"],
                    "department": user_data["department_name"]
                },
                "existing_user": True
            })

        # Step 2: Register new user
        insert_data = {
            "full_name": user.fullName,
            "mobile_no": user.mobile,
            "employee_id": user.employeeId,
            "department_name": user.department
        }

        result = supabase.table("employees").insert(insert_data).execute()
        user_id = result.data[0]["id"]

        return jsonify({
            "user_id": user_id,
            "message": "Registration successful",
            "existing_user": False
        })

    except Exception as e:
        print("Registration error:", e)
        return jsonify({"error": str(e)}), 500



@app.route("/api/check-status", methods=["POST"])
def check_status():
    try:
        data = request.json
        status_request = CheckStatusRequest(**request.json)
        user_id = data.get("user_id")
        today = date.today().isoformat()

        # Step 1: Get actual employee_id from employees table (like check-in/check-out)
        emp_lookup = supabase.table("employees") \
            .select("employee_id") \
            .eq("id", user_id) \
            .execute()

        if not emp_lookup.data:
            return jsonify({"error": "Employee not found"}), 404

        employee_id = emp_lookup.data[0]["employee_id"]

        # Step 2: Query attendance using employee_id
        res = supabase.table("attendance") \
            .select("check_in_time, check_out_time") \
            .eq("employee_id", employee_id) \
            .eq("date", today) \
            .execute()
        
        if not res.data:
            return jsonify({"status": "not_checked_in"})

        row = res.data[0]
        if row["check_in_time"] and not row["check_out_time"]:
            return jsonify({
                "status": "checked_in",
                "check_in_time": row["check_in_time"]
            })
        if row["check_in_time"] and row["check_out_time"]:
            return jsonify({
                "status": "completed",
                "check_in_time": row["check_in_time"],
                "check_out_time": row["check_out_time"]
            })        
        return jsonify({"status": "unknown"})

    except Exception as e:
        print(f"Status check error: {e}")
        return jsonify({"error": "Status check failed"}), 500



@app.route("/api/check-in", methods=["POST"])
def check_in():
    try:
        backup()
        data = request.json
        attendance = AttendanceAction(**data)
        user_id = attendance.user_id  # This is the internal `id`
        print("Check-in request:", user_id)
        today = date.today().isoformat()

        # Get actual employee_id from employees table
        emp_lookup = supabase.table("employees") \
            .select("employee_id") \
            .eq("id", user_id) \
            .execute()

        if not emp_lookup.data:
            return jsonify({"error": "Employee not found"}), 404

        employee_id = emp_lookup.data[0]["employee_id"]

        # Format location
        location_str = None
        if attendance.location:
            location_str = f"{attendance.location['latitude']},{attendance.location['longitude']}"

        # Check if already checked in
        existing = supabase.table("attendance") \
            .select("id") \
            .eq("employee_id", employee_id) \
            .eq("date", today) \
            .execute()

        if existing.data:
            return jsonify({"error": "Already checked in today"}), 400

        #Insert check-in
        check_in_data = {
            "employee_id": employee_id,
            "date": today,
            "check_in_time": datetime.now(ist).isoformat(),
            "check_in_location": location_str
        }

        supabase.table("attendance").insert(check_in_data).execute()
        backup()
        return jsonify({
            "message": "Check-in successful",
            "check_in_time": check_in_data["check_in_time"]
        })

    except Exception as e:
        print(f"Check-in error: {e}")
        return jsonify({"error": "Check-in failed"}), 500



@app.route("/api/check-out", methods=["POST"])
def check_out():
    try:
        data = request.json
        attendance = AttendanceAction(**data)
        user_id = attendance.user_id  # This is the internal `id`
        today = date.today().isoformat()

        # Step 1: Get actual employee_id from employees table
        emp_lookup = supabase.table("employees") \
            .select("employee_id") \
            .eq("id", user_id) \
            .execute()

        if not emp_lookup.data:
            return jsonify({"error": "Employee not found"}), 404

        employee_id = emp_lookup.data[0]["employee_id"]

        # Step 2: Format location
        location_str = None
        if attendance.location:
            location_str = f"{attendance.location['latitude']},{attendance.location['longitude']}"

        # Step 3: Update the attendance row where employee_id and date match and check_out_time is NULL
        update_res = supabase.table("attendance") \
            .update({
                "check_out_time": datetime.now(ist).isoformat(),
                "check_out_location": location_str
            }) \
            .eq("employee_id", employee_id) \
            .eq("date", today) \
            .is_("check_out_time", "null") \
            .execute()
        
        backup()
        if not update_res.data:
            return jsonify({"error": "No active check-in found or already checked out"}), 400
        return jsonify({
            "message": "Check-out successful",
            "check_out_time": update_res.data[0]["check_out_time"]
        })

    except Exception as e:
        print(f"Check-out error: {e}")
        return jsonify({"error": "Check-out failed"}), 500



if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
