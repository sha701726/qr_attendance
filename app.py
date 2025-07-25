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
import os

load_dotenv()
supabase = get_connection()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

app = Flask(__name__)
# CORS(app, supports_credentials=True, resources={r"/api/*": {"origins": "*"}})
CORS(app, supports_credentials=True, resources={r"/api/*": {"origins": "https://qr-attendance-sy8f.onrender.com"}})

# Helper function to get IST time
def get_indian_time():
    return datetime.now(pytz.timezone("Asia/Kolkata")).strftime("%H:%M:%S")

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/register", methods=["POST"])
def register_user():
    try:
        data = request.json
        user = UserRegister(**data)

        print("Registration request:", data)

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

        emp_lookup = supabase.table("employees") \
            .select("employee_id") \
            .eq("id", user_id) \
            .execute()

        if not emp_lookup.data:
            return jsonify({"error": "Employee not found"}), 404

        employee_id = emp_lookup.data[0]["employee_id"]

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
        user_id = attendance.user_id
        print("Check-in request:", user_id)
        today = date.today().isoformat()

        emp_lookup = supabase.table("employees") \
            .select("employee_id") \
            .eq("id", user_id) \
            .execute()

        if not emp_lookup.data:
            return jsonify({"error": "Employee not found"}), 404

        employee_id = emp_lookup.data[0]["employee_id"]

        location_str = None
        if attendance.location:
            location_str = f"{attendance.location['latitude']},{attendance.location['longitude']}"

        existing = supabase.table("attendance") \
            .select("id") \
            .eq("employee_id", employee_id) \
            .eq("date", today) \
            .execute()

        if existing.data:
            return jsonify({"error": "Already checked in today"}), 400

        check_in_data = {
            "employee_id": employee_id,
            "date": today,
            "check_in_time": get_indian_time(),
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
        user_id = attendance.user_id
        today = date.today().isoformat()

        emp_lookup = supabase.table("employees") \
            .select("employee_id") \
            .eq("id", user_id) \
            .execute()

        if not emp_lookup.data:
            return jsonify({"error": "Employee not found"}), 404

        employee_id = emp_lookup.data[0]["employee_id"]

        location_str = None
        if attendance.location:
            location_str = f"{attendance.location['latitude']},{attendance.location['longitude']}"

        update_res = supabase.table("attendance") \
            .update({
                "check_out_time": get_indian_time(),
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
