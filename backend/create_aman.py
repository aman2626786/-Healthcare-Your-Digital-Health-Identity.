import sqlite3
import os
import sys

# Append backend directory to path if needed
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app import generate_health_id, generate_health_qr, get_db_connection

def create_aman():
    health_id = generate_health_id()
    name = "Aman"
    email = "aman@demo.com"
    password = "password123"
    phone = "9876543210"
    address = "Demo Street, City"
    age = 25
    gender = "Male"
    blood_group = "O+"
    emergency_contact = "+91 9123456780"
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute('''INSERT INTO users (name, email, password, phone, address, health_id, age, gender, blood_group, emergency_contact)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    (name, email, password, phone, address, health_id, age, gender, blood_group, emergency_contact))
        conn.commit()
        print(f"SUCCESS: User created successfully!\nName: {name}\nEmail: {email}\nPhone: {phone}\nHealth ID (Username): {health_id}\nPassword: {password}")
    except Exception as e:
        print(f"ERROR: Failed to create user. Exception: {e}")
    finally:
        conn.close()
    
    try:
        qr_path = generate_health_qr(health_id)
        print(f"QR Generated at: {qr_path}")
    except Exception as e:
        print(f"ERROR generating QR: {e}")

if __name__ == "__main__":
    create_aman()
