from fastapi import FastAPI, Request
from sqlmodel import SQLModel, Field, Session, create_engine, select
from typing import Optional
from datetime import date
from dateutil.parser import parse  # For flexible date parsing
import uuid
import os
import requests

# Create uploads folder
if not os.path.exists("uploads"):
    os.makedirs("uploads")

# Database
engine = create_engine("sqlite:///./thesis.db", echo=False)

# Models
class Student(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    last_name: str
    given_name: str
    middle_initial: Optional[str] = None

class Thesis(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    title: str
    publish_date: date
    pdf_filename: str
    author_id: uuid.UUID = Field(foreign_key="student.id")

SQLModel.metadata.create_all(engine)

app = FastAPI(title="University Thesis Database")

# Handles JSON from Google Apps Script
@app.post("/submit")
async def google_forms_submit(request: Request):
    data = await request.json()

    try:
        last_name = data["Last Name"]
        given_name = data["Given Name (First Name)"]
        middle_initial = data.get("Middle Initial (optional)")
        title = data["Thesis Title"]

        # Flexible date parsing (Google Forms sends "December 18, 2025" etc.)
        date_str = data["Date of Publishing"]
        parsed_date = parse(date_str)
        publish_date = date(parsed_date.year, parsed_date.month, 1)  # We only keep month/year

        pdf_url = data["Approval Sheet + Abstract (one single PDF)"]

        with Session(engine) as session:
            # Find or create student
            student = session.exec(
                select(Student).where(
                    Student.last_name == last_name.strip(),
                    Student.given_name == given_name.strip()
                )
            ).first()

            if not student:
                student = Student(
                    last_name=last_name.strip(),
                    given_name=given_name.strip(),
                    middle_initial=middle_initial.strip() if middle_initial else None
                )
                session.add(student)
                session.commit()
                session.refresh(student)

            # Download PDF
            new_filename = f"{uuid.uuid4()}.pdf"
            file_location = f"uploads/{new_filename}"
            
            print(f"Downloading PDF from: {pdf_url}")
            response = requests.get(pdf_url, timeout=60)
            
            if response.status_code != 200:
                return {"error": f"PDF download failed (status {response.status_code})"}
            
            with open(file_location, "wb") as f:
                f.write(response.content)
            
            print(f"PDF saved as {new_filename}")

            # Save thesis
            thesis = Thesis(
                title=title.strip(),
                publish_date=publish_date,
                pdf_filename=new_filename,
                author_id=student.id
            )
            session.add(thesis)
            session.commit()

        return {"message": "Thesis saved successfully! 🎉"}

    except Exception as e:
        print(f"Error: {e}")
        return {"error": str(e)}

@app.get("/")
async def root():
    return {"message": "Thesis database server is running. Submit via Google Form → Apps Script."}