# delete_specific_thesis.py
# Deletes one specific thesis by title (case-insensitive search)
# Useful for removing bad/duplicate entries

from sqlmodel import Session, select
from main import Thesis, Student, engine

print("=== Delete Specific Thesis ===")
print("Enter the thesis title (or part of it) to delete:")
title_search = input("> ").strip()

if not title_search:
    print("No title entered. Cancelled.")
    exit()

with Session(engine) as session:
    # Find theses containing the search text (case-insensitive)
    theses = session.exec(
        select(Thesis).where(Thesis.title.ilike(f"%{title_search}%"))
    ).all()

    if not theses:
        print("No matching thesis found.")
        exit()

    print("\nFound these theses:")
    for thesis in theses:
        student = session.get(Student, thesis.author_id)
        if student:
            name = f"{student.last_name}, {student.given_name}"
            if student.middle_initial:
                name += f" {student.middle_initial}."
        else:
            name = "(Author missing)"

        print(f"ID: {thesis.id}")
        print(f"Title: {thesis.title}")
        print(f"Author: {name}")
        print(f"Published: {thesis.publish_date}")
        print("-" * 40)

    print("\nEnter the ID of the one you want to delete (or 'all' to delete all matches):")
    choice = input("> ").strip()

    to_delete = []
    if choice.lower() == "all":
        to_delete = theses
    else:
        try:
            id_num = uuid.UUID(choice)
            to_delete = [t for t in theses if t.id == id_num]
            if not to_delete:
                print("No thesis with that ID.")
                exit()
        except:
            print("Invalid ID. Cancelled.")
            exit()

    confirm = input(f"\nDelete {len(to_delete)} thesis/theses? Type 'YES' to confirm: ").strip()
    if confirm != "YES":
        print("Cancelled.")
        exit()

    for thesis in to_delete:
        session.delete(thesis)
    session.commit()

print(f"\nDeleted {len(to_delete)} thesis/theses successfully!")
print("Run 'python check_database.py' to see the updated list.")