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

        # private_key_raw =  os.getenv("GOOGLE_PRIVATE_KEY")
        private_key_raw = """-----BEGIN PRIVATE KEY-----\\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQDlSnh29PoFyNTn\\nA2NL7db2LIh71NPyf0bGljDATXGkQceih9d5gadRx++AxyJgbfVfNqccm1ZgiQIg\\nCZEoSsOG0pRLAW4Jfstz4MbekGb4K9ef1dzmIpJuuAx8FMlL2icMXg4bBjuF34Rb\\nW75dDGsP3GrZGEp9m3pMcnSzZ1sElcxjqc1DlJjJ0zZuPWEJeJFpONMpwh9m5rrA\\nwifJFJwE3qzI8le4M5TfaAvL2ftNiTwxSfkgHk1t68yM7fAyandQgOoduQRVGZch\\nII+yv758+cbTHifTECQJ88CnAJAaYv6v+l6n7dgCxkxyq+BeKj5A+E9tcUAJx4KM\\nJGlIJmlrAgMBAAECggEAC7quA+PPQGmAHpspQrKVev1XNAJ0nySMoc8ACm5LwGvP\\nAwzw5FnSDdhs84j8RLOLSEYa8Vcu6XxIvAvRPZ7pdqWiCV4220x9qt1WPv9jDRHt\\nE1OU277r/7bxiI1lqLgtpC/Rh+dfNx9yfVvplofymBqd6qIX+WnxLSTzvFOur8LD\\nI17hDqT3Y5UJScGOPH3j9TP9x2z/y2BHnwb/eF2dpBrTE8MR02E4eXi8ae1d+cJI\\nhfjZZxwOmX73anOybecdwpwiqDUtw7FBD++N8cDIGYFYN6jDAkLzZ1cMQp5YePMA\\niI3H3EiaboqX1KrknzTOyCw9ve2sna/+vmufYuqSpQKBgQD+QsTSg/Yd57XKoJtQ\\nrI7S0ijB0HlwEMiBhI2uQ0Hsz8FXAnEBfDrkPyn7h+UYyCJC3CrqJuPdCBXZJEvt\\n7eQ+fAGsMwuRF4+xy+S0qDWaAoxFTtn7UF8TabbD5xRKe8+hyqsrxjv/ShDsAcSo\\nAbnULxW7Tz8wFDiWJ2xcYueMtwKBgQDm2/o2nRok2+WwAmkPokb8KwQUmbYX4k+h\\nGcuX2TPaaTID1WJna1mQnbTaCWeMVpK+0g66EDdK0v0Xr7dcXa6HMoFcDZZG2KoZ\\nx0UavapDdXfzS016IS6NL8MlUqRyktFoTrOessYQ1fPtE/RyWYEtLGsx3d4tLYW6\\nJ4afFeP87QKBgEom3NHsTFXSYrEyf7laadjQE7TagOAO9PrY1p0Q3mQa/u7KNnzR\\nZzdzuGGz8ztz+pH3NcjOCLxIhF6seDxumZcjgTVgOapZ7b1TkmKhf+hnf9MiuO3T\\nNbcqqHOfq8pBK3+q5JrCmHLOffrmVR0OS8y24qaa6PmznAEmhDK5YYAnAoGAaESy\\nnjgWts8azoRIL2d76CkFjsheFiuBC6I68jqH0P3yOQkHiO5TZZ3VMSVOP3RakxUM\\n0bzBPGpPJYOXrYAic627/3ejiBwTt9DoxUsku5MyuhAoziBuhhYsbY8F9zmYmyPw\\nvJzCGJiJs2pv3bXPQjftsngjAQSugYWYqAGbF4ECgYEA9kgMTMtS7NRYStLuAt6S\\nsCUjPwNb+HNWA0l+mGu95EuihdJ3cVTsJnEAyaH+nDXn7JMVoSLKV+/BEc9vf/p1\\nZGPzDdmGahXs79w92YE0oog+eC4y4g4wnhY6qj/4vixXY9ZVfIvuYZBJqtF+TUkQ\\nbh2tljusySjT5YwVMbouJfA=\\n-----END PRIVATE KEY-----\\n"""
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
