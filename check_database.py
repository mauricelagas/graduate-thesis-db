from sqlmodel import Session, create_engine, select
from main import Student, Thesis
import os

engine = create_engine("sqlite:///./thesis.db")

print("=== THESIS DATABASE CONTENTS ===\n")

with Session(engine) as session:
    results = session.exec(
        select(Thesis, Student)
        .join(Student, Thesis.author_id == Student.id)
    ).all()

    if not results:
        print("No theses yet.")
    else:
        for thesis, student in results:
            name = f"{student.last_name}, {student.given_name}"
            if student.middle_initial:
                name += f" {student.middle_initial}."
            pdf_path = f"uploads/{thesis.pdf_filename}"
            exists = "✅ YES" if os.path.exists(pdf_path) else "❌ NO"

            print(f"Title: {thesis.title}")
            print(f"Author: {name}")
            print(f"Published: {thesis.publish_date.strftime('%B %Y')}")
            print(f"PDF: {thesis.pdf_filename} ({exists})")
            print("-" * 50)