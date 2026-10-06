# Graduate Thesis Database System

A practical database application for collecting, storing, and managing graduate thesis dissertation records.

Built as a personal project to solve a real administrative need: tracking thesis submissions with student details, titles, publication dates, and supporting documents (approval sheet + abstract).

## What It Does

- Accepts thesis submissions (originally via Google Forms → Google Sheets / Apps Script)
- Stores structured student and thesis data in a relational database
- Downloads and stores the approval sheet + abstract PDF
- Forces publication date to year + month only (day set to 1st) because most submitters only remember the month
- Provides simple admin scripts to inspect and clean data

## Database Design

### Tables

**Student**
| Column          | Type          | Notes                          |
|-----------------|---------------|--------------------------------|
| id              | UUID (PK)     | Auto-generated                 |
| last_name       | String        | Required                       |
| given_name      | String        | Required                       |
| middle_initial  | String        | Optional                       |

**Thesis**
| Column          | Type          | Notes                                      |
|-----------------|---------------|--------------------------------------------|
| id              | UUID (PK)     | Auto-generated                             |
| title           | String        | Thesis title                               |
| publish_date    | Date          | Stored as YYYY-MM-01 (month + year only)   |
| pdf_filename    | String        | Local filename of the downloaded PDF       |
| author_id       | UUID (FK)     | References Student.id                      |

### Key Design Decisions

1. **Month + Year only for publication date**  
   Full calendar dates were unnecessary. Most people remember the month the thesis was published, not the exact day. The system accepts various date formats and normalizes everything to the 1st of the month. This reduced user friction and kept the data clean.

2. **Separate Student and Thesis tables**  
   One student can have multiple theses. Using a foreign key keeps the data normalized and avoids repeating name information.

3. **UUID primary keys**  
   Safer for distributed systems and future expansion than auto-increment integers.

4. **PDF storage**  
   Approval sheet + abstract are stored as files. The database only keeps the filename reference.

## Tech Stack

- **Backend**: FastAPI
- **ORM / Models**: SQLModel (built on SQLAlchemy + Pydantic)
- **Database**: SQLite (easy to run locally; can be swapped for MySQL/PostgreSQL)
- **External**: Google Sheets + Google Drive API for data import and PDF download
- **Language**: Python 3

## Project Structure

```
Thesis_Portfolio/
├── main.py                 # FastAPI app + database models
├── import_from_sheet.py    # Script to pull submissions from Google Sheet
├── check_database.py       # View all stored theses and authors
├── delete_specific_thesis.py
├── delete_all_data.py
├── requirements.txt
├── thesis.db               # Sample SQLite database (empty or with test data)
└── uploads/                # Folder where PDFs are saved
```

## How to Run Locally

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.  
Submit endpoint: `POST /submit` (expects JSON from Google Apps Script or similar).

## Lessons Learned

- Linking Google Forms directly to a real database is not straightforward on free tiers. Using Google Sheets as an intermediate store + a scheduled import script was a practical workaround.
- Date handling needs to be flexible when users type free-text or use different formats.
- Keeping admin utility scripts (check, delete, import) made testing and cleanup much faster during development.

## Future Improvements

- Swap SQLite for MySQL or PostgreSQL for multi-user production use
- Add basic authentication / admin panel
- Generate simple reports (theses by year, by author, etc.)
- Better file validation and virus scanning for uploaded PDFs

---

**Author**: Maurice H. Lagas  
BS Computer Science – Technological University of the Philippines (2024)
