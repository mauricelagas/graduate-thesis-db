# import_from_sheet.py
# Pulls new thesis submissions from Google Sheet and saves them to your local database

import requests
from datetime import date
from sqlmodel import Session, select
from main import Student, Thesis, engine  # Your existing models & engine
import uuid
import os
from googleapiclient.discovery import build
from google.oauth2 import service_account
from dateutil.parser import parse  # For flexible date parsing

# === CONFIG ===
# Replace these with your own values if you want to run the Google Sheets import
SHEET_ID = "YOUR_GOOGLE_SHEET_ID_HERE"
RANGE_NAME = "Thesis Submissions"
SERVICE_JSON = "service-account.json"  # Place your own service account JSON here (never commit real credentials)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly"
]

# === AUTHENTICATION ===
credentials = service_account.Credentials.from_service_account_file(SERVICE_JSON, scopes=SCOPES)
sheets_service = build("sheets", "v4", credentials=credentials)
drive_service = build("drive", "v3", credentials=credentials)  # For reliable PDF download

# === PULL ALL RESPONSES ===
sheet = sheets_service.spreadsheets()
result = sheet.values().get(spreadsheetId=SHEET_ID, range=RANGE_NAME).execute()
rows = result.get("values", [])

if not rows:
    print("No data found in the Sheet yet.")
    exit()

headers = rows[0]
print(f"Sheet headers: {headers}")

# Find column indices using your EXACT current headers
try:
    last_name_col   = headers.index("Last Name")
    given_name_col  = headers.index("First Name")
    middle_col      = headers.index("Middle Initial (optional)")
    title_col       = headers.index("Thesis Title")
    date_col        = headers.index("Date of Publishing")
    pdf_col         = headers.index("Approval Sheet and Abstract")
except ValueError as e:
    print(f"Error finding column: {e}")
    print("Current headers:", headers)
    print("Please double-check question titles in Google Form match exactly.")
    exit()

# === PROCESS EACH ROW ===
saved_count = 0

for row in rows[1:]:  # Skip header row
    if len(row) <= pdf_col:
        continue  # Skip incomplete rows

    last_name = row[last_name_col].strip()
    given_name = row[given_name_col].strip()
    middle_initial = row[middle_col].strip() if len(row) > middle_col else ""
    title = row[title_col].strip()

    # Date parsing
    date_str = row[date_col].strip()
    try:
        # Try MM/DD/YYYY
        month, day, year = date_str.split("/")
        publish_date = date(int(year), int(month), 1)
    except:
        try:
            # Fallback: month name or other formats
            parsed = parse(date_str)
            publish_date = date(parsed.year, parsed.month, 1)
        except:
            print(f"Skipping row - bad date: {date_str}")
            continue

    pdf_link = row[pdf_col].strip()
    if not pdf_link:
        print("Skipping row - no PDF link")
        continue

    # Extract file ID from link
    file_id = ""
    if "id=" in pdf_link:
        file_id = pdf_link.split("id=")[-1].split("&")[0]
    elif "/d/" in pdf_link:
        file_id = pdf_link.split("/d/")[1].split("/")[0]

    if not file_id:
        print("Skipping row - invalid PDF link")
        continue

    # Download PDF using Drive API (reliable, no virus scan page)
    new_filename = f"{uuid.uuid4()}.pdf"
    file_location = f"uploads/{new_filename}"

    try:
        request = drive_service.files().get_media(fileId=file_id)
        response = request.execute()
        with open(file_location, "wb") as f:
            f.write(response)
        print(f"Downloaded PDF via Drive API: {new_filename}")
    except Exception as e:
        print(f"Drive API download failed: {e}")
        continue

    # Save to database
    with Session(engine) as session:
        student = session.exec(
            select(Student).where(
                Student.last_name == last_name,
                Student.given_name == given_name
            )
        ).first()

        if not student:
            student = Student(
                last_name=last_name,
                given_name=given_name,
                middle_initial=middle_initial or None
            )
            session.add(student)
            session.commit()
            session.refresh(student)

        # Skip duplicates (same title + same author)
        existing = session.exec(
            select(Thesis).where(
                Thesis.title == title,
                Thesis.author_id == student.id
            )
        ).first()
        if existing:
            print(f"Skipping duplicate: {title}")
            continue

        thesis = Thesis(
            title=title,
            publish_date=publish_date,
            pdf_filename=new_filename,
            author_id=student.id
        )
        session.add(thesis)
        session.commit()

    saved_count += 1
    print(f"Saved: {title} by {last_name}, {given_name}")

print(f"\nImport complete! {saved_count} new theses saved.")
print("Run 'python check_database.py' to verify.")