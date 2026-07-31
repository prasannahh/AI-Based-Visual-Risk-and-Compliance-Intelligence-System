"""
init_db.py
----------
Run this ONCE (or any time you want to make sure tables exist) with:

    python init_db.py

It connects to PostgreSQL using the credentials in your .env file and
creates every table defined in database.py if they don't already exist.
"""

from database import init_db, DATABASE_URL

if __name__ == "__main__":
    print(f"Connecting to: {DATABASE_URL.split('@')[-1]}")
    try:
        init_db()
        print("✅ Success! All tables were created (or already existed).")
    except Exception as e:
        print("❌ Could not connect to / initialize the database.")
        print("Error details:", e)
        print("\nCheck that:")
        print("  1. PostgreSQL is running")
        print("  2. The database named in DB_NAME exists")
        print("  3. DB_USER / DB_PASSWORD in your .env file are correct")
