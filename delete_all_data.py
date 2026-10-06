# delete_all_data.py
# Completely deletes ALL students and theses from the local database
# WARNING: This is irreversible! Use with care.

from sqlmodel import Session, delete
from main import Student, Thesis, engine

print("=== DATABASE RESET WARNING ===")
print("This script will DELETE ALL students and theses.")
print("This action cannot be undone.")
print("Type 'YES' (all caps) to confirm, or anything else to cancel.")

confirm = input("> ").strip()

if confirm != "YES":
    print("Cancelled. Nothing was deleted.")
    exit()

with Session(engine) as session:
    # Delete all theses first (due to foreign key)
    session.exec(delete(Thesis))
    # Then delete all students
    session.exec(delete(Student))
    session.commit()

print("\nDatabase cleared successfully!")
print("All students and theses have been deleted.")
print("Run 'python check_database.py' to confirm it's empty.")