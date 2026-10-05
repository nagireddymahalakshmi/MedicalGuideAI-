import sqlite3
import os


# ============================================================
# DATABASE LOCATION
# ============================================================

# The database is now outside the "medio" folder.
# This prevents Live Server from refreshing the webpage
# whenever the database changes.

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATABASE_PATH = os.path.join(
    BASE_DIR,
    "..",
    "mediguide.db"
)


# ============================================================
# CREATE DATABASE
# ============================================================

def create_database():

    connection = sqlite3.connect(DATABASE_PATH)

    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS medical_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            extracted_text TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    connection.commit()

    connection.close()


# ============================================================
# SAVE MEDICAL REPORT
# ============================================================

def save_report(filename, extracted_text):

    connection = sqlite3.connect(DATABASE_PATH)

    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO medical_reports
        (filename, extracted_text)
        VALUES (?, ?)
    """, (filename, extracted_text))

    connection.commit()

    connection.close()


# ============================================================
# GET LATEST MEDICAL REPORT
# ============================================================

def get_latest_report():

    connection = sqlite3.connect(DATABASE_PATH)

    cursor = connection.cursor()

    cursor.execute("""
        SELECT filename, extracted_text, created_at
        FROM medical_reports
        ORDER BY id DESC
        LIMIT 1
    """)

    report = cursor.fetchone()

    connection.close()

    return report


# ============================================================
# CREATE DATABASE WHEN THIS FILE IS RUN
# ============================================================

create_database()