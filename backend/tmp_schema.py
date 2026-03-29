import sqlite3
import os

db_path = os.path.join(r"e:\Swasthya-Sampark---Emergency-Response-Data-Management-System-main\backend", "health_system.db")
con = sqlite3.connect(db_path)
tables = con.execute("SELECT sql FROM sqlite_master WHERE type='table'").fetchall()
with open("schema.txt", "w") as f:
    for t in tables:
        if t[0]:
            f.write(t[0] + "\n---\n")
