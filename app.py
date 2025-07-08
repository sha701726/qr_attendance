# # app.py
# from flask import Flask, request, jsonify, render_template
# from flask_cors import CORS
# from datetime import datetime, date
# import mysql.connector
# from database import get_connection
# from yourData import export_to_google_sheet as backup

# app = Flask(__name__)
# CORS(app, supports_credentials=True, resources={r"/api/*": {"origins": "*"}})

# # Simple data classes instead of importing from models
# class UserRegister:
#     def __init__(self, fullName, mobile, employeeId, department):
#         self.fullName = fullName
#         self.mobile = mobile
#         self.employeeId = employeeId
#         self.department = department

# class AttendanceAction:
#     def __init__(self, user_id, location=None, **kwargs):
#         self.user_id = user_id
#         self.location = location
#         # Ignore any other fields like qr_code

# class CheckStatusRequest:
#     def __init__(self, user_id):
#         self.user_id = user_id

# @app.route("/")
# def home():
#     return render_template("index.html")

# @app.route("/api/register", methods=["POST"])
# def register_user():
#     conn = None
#     cursor = None
#     try:
#         data = request.json
#         print("Registration request:", data)
        
#         user = UserRegister(**data)
        
#         conn = get_connection()
#         if conn is None:
#             return jsonify({"error": "Database connection failed"}), 500

#         cursor = conn.cursor(dictionary=True)
        
#         # Check if user already exists
#         cursor.execute("SELECT id, full_name, mobile_no, employee_id, department_name FROM employees WHERE employee_id = %s", (user.employeeId,))
#         existing_user = cursor.fetchone()
        
#         if existing_user:
#             # User already exists, return their information
#             print(f"User already exists with ID: {existing_user['id']}")
#             return jsonify({
#                 "user_id": existing_user['id'],
#                 "message": "User already registered",
#                 "user_data": {
#                     "fullName": existing_user['full_name'],
#                     "mobile": existing_user['mobile_no'],
#                     "employeeId": existing_user['employee_id'],
#                     "department": existing_user['department_name']
#                 },
#                 "existing_user": True
#             })
        
#         # Insert new user
#         cursor.execute("""
#             INSERT INTO employees (full_name, mobile_no, employee_id, department_name)
#             VALUES (%s, %s, %s, %s)
#         """, (user.fullName, user.mobile, user.employeeId, user.department))
        
#         conn.commit()
#         user_id = cursor.lastrowid
        
#         print(f"New user registered successfully with ID: {user_id}")
        
#         return jsonify({
#             "user_id": user_id,
#             "message": "Registration successful",
#             "existing_user": False
#         })
        
#     except mysql.connector.Error as err:
#         print(f"Database error: {err}")
#         return jsonify({"error": f"Database error: {str(err)}"}), 500
#     except Exception as e:
#         print(f"Registration error: {e}")
#         return jsonify({"error": "Registration failed"}), 500
#     finally:
#         if cursor:
#             cursor.close()
#         if conn:
#             conn.close()

# @app.route("/api/check-status", methods=["POST"])
# def check_status():
#     conn = None
#     cursor = None
#     try:
#         data = request.json
#         status_request = CheckStatusRequest(**data)
        
#         conn = get_connection()
#         if conn is None:
#             return jsonify({"error": "Database connection failed"}), 500
            
#         cursor = conn.cursor(dictionary=True)
        
#         today = date.today()
#         cursor.execute("""
#             SELECT check_in_time, check_out_time FROM attendance
#             WHERE employee_id = %s AND date = %s
#         """, (status_request.user_id, today))
        
#         row = cursor.fetchone()
        
#         if not row:
#             return jsonify({"status": "not_checked_in"})
        
#         if row["check_in_time"] and not row["check_out_time"]:
#             return jsonify({
#                 "status": "checked_in",
#                 "check_in_time": row["check_in_time"].isoformat()
#             })
        
#         if row["check_in_time"] and row["check_out_time"]:
#             return jsonify({
#                 "status": "completed",
#                 "check_in_time": row["check_in_time"].isoformat(),
#                 "check_out_time": row["check_out_time"].isoformat()
#             })
        
#         return jsonify({"status": "unknown"})
        
#     except mysql.connector.Error as err:
#         print(f"Database error: {err}")
#         return jsonify({"error": f"Database error: {str(err)}"}), 500
#     except Exception as e:
#         print(f"Status check error: {e}")
#         return jsonify({"error": "Status check failed"}), 500
#     finally:
#         if cursor:
#             cursor.close()
#         if conn:
#             conn.close()

# @app.route("/api/check-in", methods=["POST"])
# def check_in():
#     conn = None
#     cursor = None
#     try:
#         data = request.json
#         print("Check-in request:", data)
        
#         # Create attendance object, ignoring qr_code if present.
#         raw_location = data.get('location')

#         # Extract only latitude and longitude if location is a dict
#         if isinstance(raw_location, dict):
#             location_str = f"{raw_location['latitude']},{raw_location['longitude']}"
#         else:
#             location_str = None  # or handle error/log

#         attendance = AttendanceAction(
#             user_id=data.get('user_id'),
#             location=location_str
#         )

#         print(f"Processing check-in for user ID: {attendance.user_id}, location: {attendance.location}")
        
#         conn = get_connection()
#         if conn is None:
#             return jsonify({"error": "Database connection failed"}), 500
            
#         cursor = conn.cursor()
        
#         today = date.today()
        
#         # Check if already checked in today
#         cursor.execute("SELECT id FROM attendance WHERE employee_id = %s AND date = %s", (attendance.user_id, today))
        
#         if cursor.fetchone():
#             return jsonify({"error": "Already checked in today"}), 400
        
#         # Insert check-in record (without qr_code column)
#         cursor.execute("""
#             INSERT INTO attendance (employee_id, check_in_time, check_in_location, date)
#             VALUES (%s, %s, %s, %s)
            
#         """, (
#             attendance.user_id,
#             datetime.now(),
#             str(attendance.location) if attendance.location else None,
#             today
#         ))
        
#         conn.commit()
        
#         print(f"Check-in successful for user ID: {attendance.user_id}")
#         backup()
        
#         return jsonify({
#             "message": "Check-in successful",
#             "check_in_time": datetime.now().isoformat()
#         })
        
#     except mysql.connector.Error as err:
#         print(f"Database error: {err}")
#         return jsonify({"error": f"Database error: {str(err)}"}), 500
#     except Exception as e:
#         print(f"Check-in error: {e}")
#         return jsonify({"error": "Check-in failed"}), 500
#     finally:
#         if cursor:
#             cursor.close()
#         if conn:
#             conn.close()

# @app.route("/api/check-out", methods=["POST"])
# def check_out():
#     conn = None
#     cursor = None
#     try:
#         data = request.json
#         print("Check-out request:", data)
        
#                # Create attendance object, ignoring qr_code if present.
#         raw_location = data.get('location')

#         # Extract only latitude and longitude if location is a dict
#         if isinstance(raw_location, dict):
#             location_str = f"{raw_location['latitude']},{raw_location['longitude']}"
#         else:
#             location_str = None  # or handle error/log

#         attendance = AttendanceAction(
#             user_id=data.get('user_id'),
#             location=location_str
#         )

#         print(f"Processing check-in for user ID: {attendance.user_id}, location: {attendance.location}")
        
        
#         conn = get_connection()
#         if conn is None:
#             return jsonify({"error": "Database connection failed"}), 500
            
#         cursor = conn.cursor()
        
#         today = date.today()
        
#         # Update check-out time
#         cursor.execute("""
#             UPDATE attendance
#             SET check_out_time = %s, check_out_location = %s
#             WHERE employee_id = %s AND date = %s AND check_out_time IS NULL
#         """, (
#             datetime.now(),
#             str(attendance.location) if attendance.location else None,
#             attendance.user_id,
#             today
#         ))
        
#         conn.commit()
        
#         if cursor.rowcount == 0:
#             return jsonify({"error": "No active check-in found or already checked out"}), 400
        
#         print(f"Check-out successful for user ID: {attendance.user_id}")
#         backup()
        
#         return jsonify({
#             "message": "Check-out successful",
#             "check_out_time": datetime.now().isoformat()
#         })
        
#     except mysql.connector.Error as err:
#         print(f"Database error: {err}")
#         return jsonify({"error": f"Database error: {str(err)}"}), 500
#     except Exception as e:
#         print(f"Check-out error: {e}")
#         return jsonify({"error": "Check-out failed"}), 500
#     finally:
#         if cursor:
#             cursor.close()
#         if conn:
#             conn.close()

# if __name__ == "__main__":
#     app.run(debug=True, host='0.0.0.0', port=5000)

# app.py
from Backup import export_to_google_sheet as backup
from models import UserRegister, AttendanceAction, CheckStatusRequest
from flask import Flask, request, jsonify, render_template
from database import get_connection
from flask_cors import CORS
from datetime import datetime, date
from supabase import create_client
from dotenv import load_dotenv
import os

load_dotenv()
supabase = get_connection()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

app = Flask(__name__)
CORS(app, supports_credentials=True, resources={r"/api/*": {"origins": "*"}})


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
        data = request.json
        attendance = AttendanceAction(**data)
        user_id = attendance.user_id  # This is the internal `id`
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
            "check_in_time": datetime.now().isoformat(),
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
                "check_out_time": datetime.now().isoformat(),
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
