#Only for excel;
# import mysql.connector
# from openpyxl import Workbook
# from database import get_connection

# def export_to_excel():
#     conn = get_connection()
#     cursor = conn.cursor()

#     try:
#         query = """
#             SELECT 
#                 e.id AS employee_id,
#                 e.full_name,
#                 e.mobile_no,
#                 e.employee_id AS emp_code,
#                 e.department_name,
#                 a.date,
#                 a.check_in_time,
#                 a.check_in_location,
#                 a.check_out_time,
#                 a.check_out_location
#             FROM 
#                 employees e
#             INNER JOIN 
#                 attendance a
#             ON 
#                 e.id = a.employee_id
#             ORDER BY 
#                 a.date DESC
#         """

#         cursor.execute(query)
#         rows = cursor.fetchall()
#         headers = [desc[0] for desc in cursor.description]

#         wb = Workbook()
#         ws = wb.active
#         ws.title = "Attendance Report"

#         # Write headers and rows
#         ws.append(headers)
#         for row in rows:
#             ws.append(row)

#         # Save the Excel file
#         wb.save("merged_attendance_report.xlsx")
#         print("Excel file 'merged_attendance_report.xlsx' created successfully.")

#     except mysql.connector.Error as err:
#         print(f"Error exporting to Excel: {err}")
#     finally:
#         cursor.close()
#         conn.close()

# if __name__ == "__main__":
#     export_to_excel()

#Only for Google Sheets;

#----------------------------------------------------------------------------------------------------------------------
# import mysql.connector
# import gspread
# from datetime import date, datetime, time
# from oauth2client.service_account import ServiceAccountCredentials
# from database import get_connection  # your existing DB connection logic

# def export_to_google_sheet():
#     conn = get_connection()
#     cursor = conn.cursor()

#     try:
#         # SQL query to get employee + attendance data
#         query = """
#             SELECT 
#                 e.id AS employee_id,
#                 e.full_name,
#                 e.mobile_no,
#                 e.employee_id AS emp_code,
#                 e.department_name,
#                 a.date,
#                 a.check_in_time,
#                 a.check_in_location,
#                 a.check_out_time,
#                 a.check_out_location
#             FROM 
#                 employees e
#             INNER JOIN 
#                 attendance a
#             ON 
#                 e.id = a.employee_id
#             ORDER BY 
#                 a.date DESC
#         """

#         cursor.execute(query)
#         rows = cursor.fetchall()
#         headers = [desc[0] for desc in cursor.description]

#         # === Google Sheets API setup ===
#         scope = [
#             "https://www.googleapis.com/auth/spreadsheets",
#             "https://www.googleapis.com/auth/drive"
#         ]
#         creds = ServiceAccountCredentials.from_json_keyfile_name("service_account.json", scope)
#         client = gspread.authorize(creds)

#         # Open the Google Sheet by name (make sure the name is correct)
#         sheet = client.open("qr_attendance_data").sheet1

#         # Clear old data
#         sheet.clear()

#         # Add headers
#         sheet.append_row(headers)

#         # Helper to convert any date/time fields to stringc
#         def convert_row(row):
#             return [str(item) if isinstance(item, (date, datetime, time)) else item for item in row]

#         # Add data rows
#         for row in rows:
#             sheet.append_row(convert_row(row))

#         print("Data successfully synced to Google Sheet.")

#     except mysql.connector.Error as err:
#         print(f"MySQL Error: {err}")
#     except Exception as err:
#         print(f"Google Sheets Error: {err}")
#     finally:
#         cursor.close()
#         conn.close()

# if __name__ == "__main__":
#     export_to_google_sheet()
#----------------------------------------------------------------------------------------------------------------------

# export_to_google_sheet.py
import gspread
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials
from database import get_supabase_client


def export_to_google_sheet():
    supabase = get_supabase_client()
    if not supabase:
        print(" Failed to connect to Supabase")
        return

    try:
        # Fetch employee + attendance data with JOIN
        response = supabase.table("employees").select("""
            id,
            full_name,
            mobile_no,
            employee_id,
            department_name,
            attendance:attendance!employee_id(
                date,
                check_in_time,
                check_in_location,
                check_out_time,
                check_out_location
            )
        """).execute()

        employees = response.data
        if not employees:
            print(" No employee data found.")
            return

        # Prepare headers and rows
        headers = [
            "record_id", "full_name", "mobile_no", "employee_id", "department",
            "date", "check_in_time", "check_in_location", "check_out_time", "check_out_location"
        ]
        rows = []

        for emp in employees:
            for att in emp.get("attendance", []):
                rows.append([
                    emp["id"],
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

        # Connect to Google Sheets
        scope = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = ServiceAccountCredentials.from_json_keyfile_name("service_account.json", scope)
        client = gspread.authorize(creds)

        # Open target sheet
        sheet = client.open("qr_attendance_data").sheet1

        # Write data
        sheet.clear()
        sheet.append_row(headers)
        for row in rows:
            sheet.append_row([str(item) if item else "" for item in row])

        print(f" {len(rows)} attendance records exported successfully to Google Sheet.")

    except Exception as e:
        print(f" Export error: {e}")

if __name__ == "__main__":
    export_to_google_sheet()