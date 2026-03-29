import sqlite3
import os

db_path = os.path.join(r"e:\Swasthya-Sampark---Emergency-Response-Data-Management-System-main\backend", "health_system.db")
con = sqlite3.connect(db_path)
cur = con.cursor()

columns_to_add = [
    ("latitude", "REAL"),
    ("longitude", "REAL"),
    ("abha_connected", "INTEGER DEFAULT 1")
]

added = []
for col_name, col_type in columns_to_add:
    try:
        cur.execute(f"ALTER TABLE hospitals ADD COLUMN {col_name} {col_type}")
        added.append(col_name)
    except sqlite3.OperationalError as e:
        print(f"Column {col_name} already exists or error: {e}")

con.commit()
if added:
    print(f"Successfully added columns: {', '.join(added)}")
else:
    print("No new columns added.")

con.close()
