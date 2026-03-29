import sqlite3
import os

def check_database():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_dir, 'backend', 'health_system.db')
    if not os.path.exists(db_path):
        print(f"Database file not found at: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        # Check if users table exists
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users';")
        if not cur.fetchone():
            print("Users table not found in the database.")
            return
        
        # Check for demo user
        demo_id = 'H-0000-0000'
        cur.execute('SELECT * FROM users WHERE health_id = ?', (demo_id,))
        user = cur.fetchone()
        
        if user:
            print(f"Demo user found!")
            print(f"Health ID: {user['health_id']}")
            print(f"Password: {user['password']}")
            phone = user['phone'] if 'phone' in user.keys() else None
            print(f"Phone: {phone if phone else 'Not set'}")
        else:
            print(f"Demo user with Health ID '{demo_id}' not found in the database.")
            
            # List all users for debugging
            print("\nAll users in the database:")
            cur.execute('SELECT health_id, password, phone FROM users')
            for row in cur.fetchall():
                phone = row['phone'] if 'phone' in row.keys() else None
                print(f"- Health ID: {row['health_id']}, Password: {row['password']}, Phone: {phone if phone else 'N/A'}")
        
        conn.close()
        
    except Exception as e:
        print(f"Error accessing database: {e}")

if __name__ == '__main__':
    check_database()
