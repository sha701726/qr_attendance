# Backup.py
import gspread
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials
from database import get_connection
from dotenv import load_dotenv
import os

load_dotenv()

def export_to_google_sheet():
    supabase = get_connection()
    if not supabase:
        print("Failed to connect to Supabase.")
        return

    try:
        # Step 1: Fetch employee & attendance data
        print("Fetching employees...")
        emp_response = supabase.table("employees").select("*").execute()
        employees = emp_response.data
        if not employees:
            print("No employee data found.")
            return
        print(f"Found {len(employees)} employees")

        print("Fetching attendance records...")
        att_response = supabase.table("attendance").select("*").execute()
        attendance_records = att_response.data
        print(f"Found {len(attendance_records)} attendance records")

        emp_dict = {emp["employee_id"]: emp for emp in employees}

        headers = [
            "full_name", "mobile_no", "employee_id", "department_name",
            "date", "check_in_time", "check_in_location", "check_out_time", "check_out_location"
        ]
        rows = []

        for att in attendance_records:
            emp = emp_dict.get(att["employee_id"])
            if emp:
                rows.append([
                    emp["full_name"],
                    emp["mobile_no"],
                    emp["employee_id"],
                    emp["department_name"],
                    att["date"],
                    att["check_in_time"],
                    att["check_in_location"],
                    att["check_out_time"],
                    att["check_out_location"]
                ])
            else:
                print(f"Warning: No employee found for employee_id {att['employee_id']}")

        print(f"Prepared {len(rows)} rows for export")

        private_key_raw =  os.getenv("GOOGLE_PRIVATE_KEY")
        private_key_raw = private_key_raw.replace("\\n","\n")
        service_account_data = {
            "type": os.getenv("GCP_TYPE"),
            "project_id": os.getenv("GCP_PROJECT_ID"),
            "private_key_id": os.getenv("GCP_PRIVATE_KEY_ID"),
            "private_key": private_key_raw,
            "client_email": os.getenv("GCP_CLIENT_EMAIL"),
            "client_id": os.getenv("GCP_CLIENT_ID"),
            "auth_uri": os.getenv("GCP_AUTH_URI"),
            "token_uri": os.getenv("GCP_TOKEN_URI"),
            "auth_provider_x509_cert_url": os.getenv("GCP_AUTH_PROVIDER_CERT_URL"),
            "client_x509_cert_url": os.getenv("GCP_CLIENT_CERT_URL"),
            "universe_domain": os.getenv("GCP_UNIVERSE_DOMAIN"),
        }


        scope = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]

        creds = ServiceAccountCredentials.from_json_keyfile_dict(service_account_data, scope)
        client = gspread.authorize(creds)
        print("Google Sheets client authorized successfully.")

        # Step 3: Export to Google Sheet
        sheet = client.open("qr_attendance_data").sheet1
        sheet.clear()
        sheet.append_row(headers)

        for row in rows:
            sheet.append_row([str(item) if item is not None else "" for item in row])

        print(f"Successfully exported {len(rows)} attendance records to Google Sheet.")

    except Exception as e:
        print(f"Export error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    export_to_google_sheet()
