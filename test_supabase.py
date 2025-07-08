from supabase import create_client
from dotenv import load_dotenv
import os
from datetime import datetime

# Load your .env variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Connect to Supabase
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def test_connection():
    print("Testing Supabase connection...")
    try:
        res = supabase.table("employees").select("*").limit(1).execute()
        print("Connected! Sample employee data (if any):", res.data)
    except Exception as e:
        print("Connection failed:", str(e))

def test_insert_employee():
    print("\n Inserting test employee...")
    data = {
        "full_name": "Nitin Test",
        "mobile_no": 9876543210,
        "employee_id": 123456,
        "department_name": "Testing Dept"
    }
    res = supabase.table("employees").insert(data).execute()
    print("Inserted employee data:", res.data)

def test_log_attendance():
    print("\nLogging attendance (check-in)...")
    emp_id = get_employee_id_by_employee_id(123456)

    if not emp_id:
        print("Employee not found, make sure they exist.")
        return

    date_today = datetime.now().date().isoformat()
    check_in_time = datetime.now().isoformat()

    # Check if already checked in today
    existing = supabase.table("attendance") \
        .select("*") \
        .eq("employee_id", emp_id) \
        .eq("date", date_today) \
        .execute()

    if len(existing.data) == 0:
        # Insert check-in
        res = supabase.table("attendance").insert({
            "employee_id": emp_id,
            "date": date_today,
            "check_in_time": check_in_time,
            "check_in_location": "28.6100,77.2300"
        }).execute()
        print("Check-in recorded:", res.data)
    else:
        # Update check-out
        res = supabase.table("attendance").update({
            "check_out_time": datetime.now().isoformat(),
            "check_out_location": "28.6100,77.2300"
        }).eq("employee_id", emp_id).eq("date", date_today).execute()
        print("Check-out recorded:", res.data)

def get_employee_id_by_employee_id(employee_id_value):
    res = supabase.table("employees") \
        .select("id") \
        .eq("employee_id", employee_id_value) \
        .execute()
    if res.data:
        return res.data[0]['id']
    return None

# Run the tests
if __name__ == "__main__":
    test_connection()
    test_insert_employee()
    test_log_attendance()
