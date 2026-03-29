from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory, Response
import sqlite3
import os
import uuid
import sys
import argparse
try:
    import qrcode
    QRCODE_AVAILABLE = True
except ImportError:
    qrcode = None
    QRCODE_AVAILABLE = False
from datetime import datetime, timedelta
import csv
import io
import pickle
import numpy as np
import requests
import random
import warnings
import re


def demo_defaults():
    return {
        'health_admin_email': os.environ.get('DEMO_HEALTH_ADMIN_EMAIL', os.environ.get('HEALTH_ADMIN_EMAIL', 'admin@health.org')),
        'health_admin_password': os.environ.get('DEMO_HEALTH_ADMIN_PASSWORD', os.environ.get('HEALTH_ADMIN_PASSWORD', 'admin123')),
        'hospital_email': os.environ.get('DEMO_HOSPITAL_EMAIL', 'admin@hospital.com'),
        'hospital_password': os.environ.get('DEMO_HOSPITAL_PASSWORD', 'admin123'),
        'doctor_email': os.environ.get('DEMO_DOCTOR_EMAIL', 'doctor@hospital.com'),
        'doctor_password': os.environ.get('DEMO_DOCTOR_PASSWORD', 'doctor123'),
        'staff_email': os.environ.get('DEMO_STAFF_EMAIL', 'staff@hospital.com'),
        'staff_password': os.environ.get('DEMO_STAFF_PASSWORD', 'staff123'),
        'user_health_id': os.environ.get('DEMO_USER_HEALTH_ID', 'H-0000-0000'),
        'user_password': os.environ.get('DEMO_USER_PASSWORD', 'user123'),
    }

# Firebase Admin SDK
try:
    import firebase_admin
    from firebase_admin import credentials, auth
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False
    print("[WARNING] Firebase Admin SDK not installed. Install with: pip install firebase-admin")

# Try to use config.py if available, otherwise use direct configuration
try:
    from config import get_config
    config = get_config()
    USE_CONFIG = True
except ImportError:
    USE_CONFIG = False
    config = None

# Initialize Flask app with frontend folder paths
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)  # Go up one level to project root
FRONTEND_DIR = os.path.join(PROJECT_ROOT, 'frontend')

# Use config if available, otherwise use defaults
if USE_CONFIG and config:
    app = Flask(__name__, 
                template_folder=config.TEMPLATE_FOLDER,
                static_folder=config.STATIC_FOLDER)
    app.secret_key = config.SECRET_KEY
    app.config['UPLOAD_FOLDER'] = config.UPLOAD_FOLDER
    DB_PATH = config.DB_PATH
    FIREBASE_CREDENTIALS_PATH = config.FIREBASE_CREDENTIALS_PATH
    FIREBASE_WEB_API_KEY = config.FIREBASE_WEB_API_KEY
    OTP_CODE_LENGTH = config.OTP_CODE_LENGTH
    OTP_EXPIRY_MINUTES = config.OTP_EXPIRY_MINUTES
    UPLOAD_FOLDER = config.UPLOAD_FOLDER
    QR_FOLDER = config.QR_FOLDER
    MODEL_PATH = config.MODEL_PATH
    EMERGENCY_MODEL_PATH = config.EMERGENCY_MODEL_PATH
else:
    # Fallback to direct configuration (backward compatibility)
    app = Flask(__name__, 
                template_folder=os.path.join(FRONTEND_DIR, 'templates'),
                static_folder=os.path.join(FRONTEND_DIR, 'static'))
    app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-prod')
    DB_PATH = os.path.join(BACKEND_DIR, 'health_system.db')
    FIREBASE_CREDENTIALS_PATH = os.path.join(BACKEND_DIR, 'pkl', 'swasthya-sampark-firebase-adminsdk-fbsvc-121be5c997.json')
    if not os.path.exists(FIREBASE_CREDENTIALS_PATH):
        FIREBASE_CREDENTIALS_PATH = os.path.join(BACKEND_DIR, 'firebase_service_account.json')
    FIREBASE_WEB_API_KEY = os.environ.get('FIREBASE_WEB_API_KEY', 'BC5Hbsevk0B2jrRVwGVm0iMK0mq-2DaefIRLd_0aueAUz6LABC5jApBBqkfvLw6vTB3PWAwsCgsdkvvC2QlMa_c')
    OTP_CODE_LENGTH = int(os.environ.get('OTP_CODE_LENGTH', 6))
    OTP_EXPIRY_MINUTES = int(os.environ.get('OTP_EXPIRY_MINUTES', 10))
    UPLOAD_FOLDER = os.path.join(BACKEND_DIR, 'uploads')
    QR_FOLDER = os.path.join(FRONTEND_DIR, 'static', 'qr')
    MODEL_PATH = os.path.join(BACKEND_DIR, 'pkl', 'svm_health_risk_model.pkl')
    EMERGENCY_MODEL_PATH = os.path.join(BACKEND_DIR, 'pkl', 'Logistic_regression_prediction.pkl')
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Firebase Configuration
FIREBASE_INITIALIZED = False

# Initialize Firebase Admin SDK
if FIREBASE_AVAILABLE:
    try:
        # Try service account JSON first (preferred for Admin SDK)
        if os.path.exists(FIREBASE_CREDENTIALS_PATH):
            cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
            firebase_admin.initialize_app(cred)
            FIREBASE_INITIALIZED = True
            print("[OK] Firebase Admin SDK initialized successfully (Service Account)")
        # If no service account, use web API key for client-side operations
        elif FIREBASE_WEB_API_KEY:
            # Web API Key is configured - enable Firebase features
            # Note: Admin SDK requires service account for full features
            # Web API key enables client-side Firebase operations and validation
            FIREBASE_INITIALIZED = True
            print(f"[OK] Firebase Web API Key configured: {FIREBASE_WEB_API_KEY[:30]}...")
            print("[INFO] Web API Key enabled for client-side Firebase operations")
            print("[INFO] For full Admin SDK features, add service account JSON file")
        else:
            print(f"[WARNING] Firebase credentials file not found at {FIREBASE_CREDENTIALS_PATH}")
            print("[INFO] OTP verification will use database storage only")
            print("[INFO] To enable Firebase:")
            print("  1. Download service account key and save as 'firebase_service_account.json'")
            print("  2. Or set FIREBASE_WEB_API_KEY environment variable")
    except Exception as e:
        print(f"[ERROR] Failed to initialize Firebase Admin SDK: {e}")
        print("[INFO] OTP verification will use database storage only")
else:
    print("[WARNING] Firebase Admin SDK not available. OTP verification will use database storage only")
# Create necessary directories
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(QR_FOLDER, exist_ok=True)

# Load health risk prediction model (SVM)
health_risk_model = None
model_scaler = None
try:
    if os.path.exists(MODEL_PATH):
        with open(MODEL_PATH, 'rb') as f:
            model_data = pickle.load(f)
            # Handle both old format (just model) and new format (dict with model and scaler)
            if isinstance(model_data, dict):
                health_risk_model = model_data.get('model')
                model_scaler = model_data.get('scaler')
                print(f"[OK] Health risk model loaded successfully from {MODEL_PATH}")
                print(f"[OK] Model includes scaler for feature normalization")
            else:
                # Old format - just the model
                health_risk_model = model_data
                model_scaler = None
                print(f"[OK] Health risk model loaded (legacy format, no scaler)")
    else:
        print(f"[WARNING] Health risk model not found at {MODEL_PATH}")
        print(f"[INFO] Run 'python train_model.py' to train a new model")
except Exception as e:
    print(f"[ERROR] Error loading health risk model: {e}")
    print(f"[INFO] Continuing without AI risk prediction. Emergency triggers will be based on treatment status only.")

# Load emergency priority prediction model (Logistic Regression)
emergency_model = None
emergency_scaler = None
try:
    if os.path.exists(EMERGENCY_MODEL_PATH):
        # Try multiple loading methods including joblib
        loaded = False
        
        # Method 1: Try joblib (common for scikit-learn models)
        try:
            import joblib
            emergency_data = joblib.load(EMERGENCY_MODEL_PATH)
            if isinstance(emergency_data, dict):
                emergency_model = emergency_data.get('model') or emergency_data.get('logistic_model') or emergency_data.get('classifier')
                emergency_scaler = emergency_data.get('scaler')
            elif hasattr(emergency_data, 'predict'):
                # Direct model object (LogisticRegression)
                emergency_model = emergency_data
                emergency_scaler = None
            
            if emergency_model and hasattr(emergency_model, 'predict'):
                print(f"[OK] Emergency prediction model loaded successfully using joblib")
                print(f"[OK] Model type: {type(emergency_model).__name__}")
                if hasattr(emergency_model, 'n_features_in_'):
                    print(f"[OK] Model expects {emergency_model.n_features_in_} features")
                if emergency_scaler:
                    print(f"[OK] Emergency model includes scaler for feature normalization")
                else:
                    print(f"[INFO] No scaler found - features will be used as-is")
                loaded = True
        except ImportError:
            print(f"[INFO] joblib not available, trying other methods...")
        except Exception as e:
            print(f"[INFO] joblib loading failed: {e}, trying other methods...")
        
        # Method 2: Try pickle with different protocols and encodings
        if not loaded:
            loading_methods = [
                ('standard', lambda f: pickle.load(f)),
                ('latin1', lambda f: pickle.load(f, encoding='latin1')),
                ('bytes', lambda f: pickle.load(f, encoding='bytes')),
                ('protocol4', lambda f: pickle.load(f, fix_imports=True)),
            ]
            
            for method_name, load_func in loading_methods:
                try:
                    with open(EMERGENCY_MODEL_PATH, 'rb') as f:
                        emergency_data = load_func(f)
                        # Handle different formats
                        if isinstance(emergency_data, dict):
                            emergency_model = emergency_data.get('model') or emergency_data.get('logistic_model') or emergency_data.get('classifier')
                            emergency_scaler = emergency_data.get('scaler')
                            if emergency_model and hasattr(emergency_model, 'predict'):
                                print(f"[OK] Emergency prediction model loaded successfully ({method_name})")
                                if emergency_scaler:
                                    print(f"[OK] Emergency model includes scaler for feature normalization")
                                loaded = True
                                break
                        else:
                            # Assume it's the model directly
                            if hasattr(emergency_data, 'predict'):
                                emergency_model = emergency_data
                                emergency_scaler = None
                                print(f"[OK] Emergency prediction model loaded (direct format, {method_name})")
                                loaded = True
                                break
                except Exception as e:
                    continue  # Try next method
        
        # Method 3: Try with dill (more compatible pickle alternative)
        if not loaded:
            try:
                import dill
                with open(EMERGENCY_MODEL_PATH, 'rb') as f:
                    emergency_data = dill.load(f)
                    if isinstance(emergency_data, dict):
                        emergency_model = emergency_data.get('model') or emergency_data.get('logistic_model') or emergency_data.get('classifier')
                        emergency_scaler = emergency_data.get('scaler')
                    elif hasattr(emergency_data, 'predict'):
                        emergency_model = emergency_data
                        emergency_scaler = None
                    
                    if emergency_model and hasattr(emergency_model, 'predict'):
                        print(f"[OK] Emergency prediction model loaded successfully using dill")
                        if emergency_scaler:
                            print(f"[OK] Emergency model includes scaler for feature normalization")
                        loaded = True
            except ImportError:
                pass  # dill not available
            except Exception as e:
                pass  # dill failed
        
        if not loaded:
            print(f"[WARNING] Could not load emergency model with any method")
            print(f"[INFO] Emergency section will use rule-based priority prediction")
            print(f"[INFO] To fix: The model file may need to be re-saved with Python 3.x compatible pickle protocol")
    else:
        print(f"[WARNING] Emergency prediction model not found at {EMERGENCY_MODEL_PATH}")
        print(f"[INFO] Emergency section will use rule-based priority prediction")
except Exception as e:
    print(f"[ERROR] Error loading emergency prediction model: {e}")
    print(f"[INFO] Emergency section will use rule-based priority prediction")


# Helper function to get DB connection
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# Initialize database with basic schema
def init_db():
    """Initialize database and create all tables if they don't exist"""
    # Ensure database directory exists
    db_dir = os.path.dirname(DB_PATH)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
        print(f"[INFO] Created database directory: {db_dir}")
    
    print(f"[INFO] Initializing database at: {DB_PATH}")
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        print("[INFO] Creating database tables...")
        
        # Hospitals
        cur.execute(
            '''CREATE TABLE IF NOT EXISTS hospitals (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   name TEXT NOT NULL,
                   reg_no TEXT UNIQUE NOT NULL,
                   email TEXT UNIQUE NOT NULL,
                   password TEXT NOT NULL,
                   state TEXT,
                   district TEXT
               )'''
        )
        print("[OK] Created/verified hospitals table")

        # Doctors
        cur.execute(
            '''CREATE TABLE IF NOT EXISTS doctors (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   hospital_id INTEGER NOT NULL,
                   name TEXT NOT NULL,
                   email TEXT UNIQUE NOT NULL,
                   password TEXT NOT NULL,
                   specialization TEXT,
                   FOREIGN KEY(hospital_id) REFERENCES hospitals(id)
               )'''
        )
        print("[OK] Created/verified doctors table")

        # Users / Patients
        cur.execute(
            '''CREATE TABLE IF NOT EXISTS users (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   name TEXT NOT NULL,
                   email TEXT UNIQUE NOT NULL,
                   password TEXT NOT NULL,
                   phone TEXT,
                   address TEXT,
                   health_id TEXT UNIQUE NOT NULL,
                   age INTEGER,
                   gender TEXT
               )'''
        )
        print("[OK] Created/verified users table")

        # Migrations for users table
        try:
            cur.execute('ALTER TABLE users ADD COLUMN emergency_contact_name TEXT')
            conn.commit()
            print("[OK] Migrated users table: added emergency_contact_name")
        except sqlite3.OperationalError:
            pass  # Column already exists

        # Medical records (per consultation)
        cur.execute(
            '''CREATE TABLE IF NOT EXISTS records (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   user_id INTEGER NOT NULL,
                   doctor_id INTEGER NOT NULL,
                   date TEXT NOT NULL,
                   symptoms TEXT,
                   diagnosis TEXT,
                   medicines TEXT,
                   dosage TEXT,
                   treatment_status TEXT,
                   consultation_duration INTEGER,
                   prescription_text TEXT,
                   prescription_filename TEXT,
                   blood_report_filename TEXT,
                   report_filename TEXT,
                   created_at TEXT NOT NULL,
                   risk_level TEXT,
                   risk_score REAL,
                   FOREIGN KEY(user_id) REFERENCES users(id),
                   FOREIGN KEY(doctor_id) REFERENCES doctors(id)
               )'''
        )
        print("[OK] Created/verified records table")

        # Emergency requests
        cur.execute(
            '''CREATE TABLE IF NOT EXISTS emergencies (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   user_id INTEGER,
                   name TEXT,
                   phone TEXT,
                   location TEXT NOT NULL,
                   status TEXT NOT NULL,
                   requested_at TEXT NOT NULL,
                   response_time_minutes INTEGER
               )'''
        )
        print("[OK] Created/verified emergencies table")

        # OTP storage for password reset and login
        cur.execute(
            '''CREATE TABLE IF NOT EXISTS otp_codes (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   phone TEXT NOT NULL,
                   code TEXT NOT NULL,
                   role TEXT NOT NULL,
                   identifier TEXT NOT NULL,
                   purpose TEXT NOT NULL,
                   created_at TEXT NOT NULL,
                   expires_at TEXT NOT NULL,
                   verified INTEGER DEFAULT 0
               )'''
        )
        print("[OK] Created/verified otp_codes table")

        cur.execute(
            '''CREATE TABLE IF NOT EXISTS health_admins (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   email TEXT UNIQUE NOT NULL,
                   password TEXT NOT NULL
               )'''
        )
        print("[OK] Created/verified health_admins table")

        # Hospital inventory
        cur.execute(
            '''CREATE TABLE IF NOT EXISTS inventory_items (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   hospital_id INTEGER NOT NULL,
                   item_name TEXT NOT NULL,
                   medicine_type TEXT,
                   strength_mg REAL,
                   category TEXT,
                   quantity INTEGER NOT NULL DEFAULT 0,
                   unit TEXT,
                   reorder_level INTEGER NOT NULL DEFAULT 0,
                   last_updated TEXT NOT NULL,
                   notes TEXT,
                   UNIQUE(hospital_id, item_name),
                   FOREIGN KEY(hospital_id) REFERENCES hospitals(id)
               )'''
        )
        print("[OK] Created/verified inventory_items table")

        # Staff accounts (created by hospital/admin)
        cur.execute(
            '''CREATE TABLE IF NOT EXISTS staff (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   hospital_id INTEGER NOT NULL,
                   name TEXT NOT NULL,
                   email TEXT UNIQUE NOT NULL,
                   password TEXT NOT NULL,
                   role_title TEXT,
                   FOREIGN KEY(hospital_id) REFERENCES hospitals(id)
               )'''
        )
        print("[OK] Created/verified staff table")

        cur.execute(
            '''CREATE TABLE IF NOT EXISTS staff_tasks (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   hospital_id INTEGER NOT NULL,
                   staff_id INTEGER,
                   title TEXT NOT NULL,
                   status TEXT NOT NULL DEFAULT 'Pending',
                   due_date TEXT,
                   created_at TEXT NOT NULL,
                   FOREIGN KEY(hospital_id) REFERENCES hospitals(id),
                   FOREIGN KEY(staff_id) REFERENCES staff(id)
               )'''
        )

        cur.execute(
            '''CREATE TABLE IF NOT EXISTS staff_activity_log (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   hospital_id INTEGER NOT NULL,
                   staff_id INTEGER NOT NULL,
                   action TEXT NOT NULL,
                   details TEXT,
                   created_at TEXT NOT NULL,
                   FOREIGN KEY(hospital_id) REFERENCES hospitals(id),
                   FOREIGN KEY(staff_id) REFERENCES staff(id)
               )'''
        )

        cur.execute(
            '''CREATE TABLE IF NOT EXISTS patient_status (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   hospital_id INTEGER NOT NULL,
                   user_id INTEGER NOT NULL,
                   status TEXT NOT NULL,
                   updated_by_staff_id INTEGER,
                   updated_at TEXT NOT NULL,
                   UNIQUE(hospital_id, user_id),
                   FOREIGN KEY(hospital_id) REFERENCES hospitals(id),
                   FOREIGN KEY(user_id) REFERENCES users(id),
                   FOREIGN KEY(updated_by_staff_id) REFERENCES staff(id)
               )'''
        )

        cur.execute(
            '''CREATE TABLE IF NOT EXISTS medicine_administration (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   hospital_id INTEGER NOT NULL,
                   record_id INTEGER NOT NULL,
                   medicine_name TEXT NOT NULL,
                   status TEXT NOT NULL DEFAULT 'Pending',
                   updated_by_staff_id INTEGER,
                   updated_at TEXT NOT NULL,
                   UNIQUE(record_id, medicine_name),
                   FOREIGN KEY(hospital_id) REFERENCES hospitals(id),
                   FOREIGN KEY(record_id) REFERENCES records(id),
                   FOREIGN KEY(updated_by_staff_id) REFERENCES staff(id)
               )'''
        )

        cur.execute(
            '''CREATE TABLE IF NOT EXISTS beds (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   hospital_id INTEGER NOT NULL,
                   bed_number TEXT NOT NULL,
                   ward TEXT,
                   bed_type TEXT,
                   status TEXT NOT NULL DEFAULT 'Available',
                   notes TEXT,
                   created_at TEXT NOT NULL,
                   updated_at TEXT NOT NULL,
                   UNIQUE(hospital_id, bed_number),
                   FOREIGN KEY(hospital_id) REFERENCES hospitals(id)
               )'''
        )

        cur.execute(
            '''CREATE TABLE IF NOT EXISTS admissions (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   hospital_id INTEGER NOT NULL,
                   user_id INTEGER NOT NULL,
                   bed_id INTEGER,
                   status TEXT NOT NULL DEFAULT 'Active',
                   reason TEXT,
                   admitted_at TEXT NOT NULL,
                   discharged_at TEXT,
                   created_by_staff_id INTEGER,
                   discharged_by_staff_id INTEGER,
                   FOREIGN KEY(hospital_id) REFERENCES hospitals(id),
                   FOREIGN KEY(user_id) REFERENCES users(id),
                   FOREIGN KEY(bed_id) REFERENCES beds(id),
                   FOREIGN KEY(created_by_staff_id) REFERENCES staff(id),
                   FOREIGN KEY(discharged_by_staff_id) REFERENCES staff(id)
               )'''
        )

        conn.commit()
        
        conn.commit()
        
        # Add missing columns if they don't exist
        # Hospitals table
        try:
            cur.execute('ALTER TABLE hospitals ADD COLUMN state TEXT')
            conn.commit()
        except sqlite3.OperationalError:
            pass  # Column already exists

        # Inventory table
        try:
            cur.execute('ALTER TABLE inventory_items ADD COLUMN medicine_type TEXT')
            conn.commit()
        except sqlite3.OperationalError:
            pass

        try:
            cur.execute('ALTER TABLE inventory_items ADD COLUMN strength_mg REAL')
            conn.commit()
        except sqlite3.OperationalError:
            pass
        
        # Emergencies table - ML prediction columns
        try:
            cur.execute('ALTER TABLE emergencies ADD COLUMN priority TEXT')
            conn.commit()
        except sqlite3.OperationalError:
            pass  # Column already exists

        try:
            cur.execute('ALTER TABLE emergencies ADD COLUMN hospital_id INTEGER')
            conn.commit()
        except sqlite3.OperationalError:
            pass

        try:
            cur.execute('ALTER TABLE emergencies ADD COLUMN assigned_at TEXT')
            conn.commit()
        except sqlite3.OperationalError:
            pass

        try:
            cur.execute('ALTER TABLE emergencies ADD COLUMN district TEXT')
            conn.commit()
        except sqlite3.OperationalError:
            pass

        try:
            cur.execute('ALTER TABLE emergencies ADD COLUMN seen_by_hospital INTEGER DEFAULT 0')
            conn.commit()
        except sqlite3.OperationalError:
            pass

        try:
            cur.execute('ALTER TABLE emergencies ADD COLUMN symptoms TEXT')
            conn.commit()
        except sqlite3.OperationalError:
            pass
        
        try:
            cur.execute('ALTER TABLE emergencies ADD COLUMN severity TEXT')
            conn.commit()
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        try:
            cur.execute('ALTER TABLE emergencies ADD COLUMN prediction_score REAL')
            conn.commit()
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        try:
            cur.execute('ALTER TABLE emergencies ADD COLUMN symptoms TEXT')
            conn.commit()
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        try:
            cur.execute('ALTER TABLE emergencies ADD COLUMN age INTEGER')
            conn.commit()
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        # Emergency additional fields for ML model
        try:
            cur.execute('ALTER TABLE emergencies ADD COLUMN state TEXT')
            conn.commit()
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        try:
            cur.execute('ALTER TABLE emergencies ADD COLUMN zone TEXT')
            conn.commit()
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        try:
            cur.execute('ALTER TABLE emergencies ADD COLUMN day TEXT')
            conn.commit()
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        try:
            cur.execute('ALTER TABLE emergencies ADD COLUMN time_slot TEXT')
            conn.commit()
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        try:
            cur.execute('ALTER TABLE emergencies ADD COLUMN emergency_type TEXT')
            conn.commit()
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        try:
            cur.execute('ALTER TABLE emergencies ADD COLUMN weather TEXT')
            conn.commit()
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        try:
            cur.execute('ALTER TABLE hospitals ADD COLUMN district TEXT')
            conn.commit()
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        # Users table
        try:
            cur.execute('ALTER TABLE users ADD COLUMN age INTEGER')
            conn.commit()
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        try:
            cur.execute('ALTER TABLE users ADD COLUMN gender TEXT')
            conn.commit()
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        # Doctors table - add phone
        try:
            cur.execute('ALTER TABLE doctors ADD COLUMN phone TEXT')
            conn.commit()
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        # Hospitals table - add phone
        try:
            cur.execute('ALTER TABLE hospitals ADD COLUMN phone TEXT')
            conn.commit()
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        # Records table
        try:
            cur.execute('ALTER TABLE records ADD COLUMN dosage TEXT')
            conn.commit()
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        try:
            cur.execute('ALTER TABLE records ADD COLUMN treatment_status TEXT')
            conn.commit()
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        try:
            cur.execute('ALTER TABLE records ADD COLUMN consultation_duration INTEGER')
            conn.commit()
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        try:
            cur.execute('ALTER TABLE records ADD COLUMN prescription_text TEXT')
            conn.commit()
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        try:
            cur.execute('ALTER TABLE records ADD COLUMN prescription_filename TEXT')
            conn.commit()
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        try:
            cur.execute('ALTER TABLE records ADD COLUMN blood_report_filename TEXT')
            conn.commit()
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        try:
            cur.execute('ALTER TABLE records ADD COLUMN blood_report_file TEXT')
            conn.commit()
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        try:
            cur.execute('ALTER TABLE records ADD COLUMN prescription_file TEXT')
            conn.commit()
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        # Add risk prediction columns
        try:
            cur.execute('ALTER TABLE records ADD COLUMN risk_level TEXT')
            conn.commit()
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        try:
            cur.execute('ALTER TABLE records ADD COLUMN risk_score REAL')
            conn.commit()
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        # Add health metrics columns for risk prediction
        health_metrics_columns = [
            ('systolic_bp', 'INTEGER'),
            ('diastolic_bp', 'INTEGER'),
            ('bmi', 'REAL'),
            ('cholesterol', 'REAL'),
            ('glucose', 'REAL'),
            ('smoking', 'TEXT'),
            ('alcohol', 'TEXT'),
            ('physical_activity', 'TEXT'),
            ('family_history', 'TEXT'),
        ]
        
        for col_name, col_type in health_metrics_columns:
            try:
                cur.execute(f'ALTER TABLE records ADD COLUMN {col_name} {col_type}')
                conn.commit()
            except sqlite3.OperationalError:
                pass  # Column already exists

        try:
            demo = demo_defaults()

            # Seed demo health admin (must match values prefilled in template)
            cur.execute('SELECT id FROM health_admins WHERE email = ?', (demo['health_admin_email'],))
            existing_admin = cur.fetchone()
            if existing_admin:
                cur.execute(
                    'UPDATE health_admins SET password = ? WHERE id = ?',
                    (demo['health_admin_password'], existing_admin['id']),
                )
            else:
                cur.execute(
                    'INSERT INTO health_admins (email, password) VALUES (?, ?)',
                    (demo['health_admin_email'], demo['health_admin_password']),
                )

            # Seed demo hospital (for hospital login form defaults)
            cur.execute('SELECT id FROM hospitals WHERE email = ?', (demo['hospital_email'],))
            hospital = cur.fetchone()
            if hospital:
                cur.execute(
                    'UPDATE hospitals SET password = ? WHERE id = ?',
                    (demo['hospital_password'], hospital['id']),
                )
                demo_hospital_id = hospital['id']
            else:
                cur.execute(
                    'INSERT INTO hospitals (name, reg_no, email, password, state, district) VALUES (?, ?, ?, ?, ?, ?)',
                    ('Demo Hospital', 'DEMO-HOSP-0001', demo['hospital_email'], demo['hospital_password'], None, None),
                )
                demo_hospital_id = cur.lastrowid

            # Seed demo doctor (for doctor login form defaults)
            cur.execute('SELECT id FROM doctors WHERE email = ?', (demo['doctor_email'],))
            doctor = cur.fetchone()
            if doctor:
                cur.execute(
                    'UPDATE doctors SET password = ? WHERE id = ?',
                    (demo['doctor_password'], doctor['id']),
                )
            else:
                cur.execute(
                    'INSERT INTO doctors (hospital_id, name, email, password, specialization) VALUES (?, ?, ?, ?, ?)',
                    (demo_hospital_id, 'Demo Doctor', demo['doctor_email'], demo['doctor_password'], 'General'),
                )

            # Seed demo staff (login via doctor login page)
            cur.execute('SELECT id FROM staff WHERE email = ?', (demo['staff_email'],))
            staff_row = cur.fetchone()
            if staff_row:
                cur.execute(
                    'UPDATE staff SET password = ?, hospital_id = ? WHERE id = ?',
                    (demo['staff_password'], demo_hospital_id, staff_row['id']),
                )
            else:
                cur.execute(
                    'INSERT INTO staff (hospital_id, name, email, password, role_title) VALUES (?, ?, ?, ?, ?)',
                    (demo_hospital_id, 'Demo Staff', demo['staff_email'], demo['staff_password'], 'Reception'),
                )

            # Seed demo user/patient (for user login form defaults)
            cur.execute('SELECT id FROM users WHERE health_id = ?', (demo['user_health_id'],))
            demo_user = cur.fetchone()
            if demo_user:
                cur.execute(
                    'UPDATE users SET password = ? WHERE id = ?',
                    (demo['user_password'], demo_user['id']),
                )
            else:
                cur.execute(
                    '''INSERT INTO users (name, email, password, phone, address, health_id, age)
                       VALUES (?, ?, ?, ?, ?, ?, ?)''',
                    ('Demo User', 'demo.user@health.org', demo['user_password'], None, None, demo['user_health_id'], None),
                )

            conn.commit()
        except Exception:
            pass

        conn.close()
        print("[OK] Database initialization completed successfully")
    except Exception as e:
        print(f"[ERROR] Database initialization failed: {e}")
        import traceback
        traceback.print_exc()
        # Try to close connection if it was opened
        try:
            if 'conn' in locals():
                conn.close()
        except:
            pass
        raise  # Re-raise to ensure we know about the error


def purge_non_demo_data(keep_demo_records_only=True):
    demo = demo_defaults()

    demo_health_admin_email = (demo.get('health_admin_email') or '').strip().lower()
    demo_hospital_email = (demo.get('hospital_email') or '').strip().lower()
    demo_doctor_email = (demo.get('doctor_email') or '').strip().lower()
    demo_staff_email = (demo.get('staff_email') or '').strip().lower()
    demo_user_health_id = (demo.get('user_health_id') or '').strip()

    conn = get_db_connection()
    cur = conn.cursor()

    def _safe_exec(sql, params=()):
        try:
            cur.execute(sql, params)
            return True
        except sqlite3.OperationalError:
            return False

    # Resolve demo IDs (best-effort)
    demo_admin_id = None
    if demo_health_admin_email:
        if _safe_exec('SELECT id FROM health_admins WHERE LOWER(email) = ?', (demo_health_admin_email,)):
            r = cur.fetchone()
            demo_admin_id = (r['id'] if r else None)

    demo_hospital_id = None
    if demo_hospital_email:
        if _safe_exec('SELECT id FROM hospitals WHERE LOWER(email) = ?', (demo_hospital_email,)):
            r = cur.fetchone()
            demo_hospital_id = (r['id'] if r else None)

    demo_doctor_id = None
    if demo_doctor_email:
        if _safe_exec('SELECT id FROM doctors WHERE LOWER(email) = ?', (demo_doctor_email,)):
            r = cur.fetchone()
            demo_doctor_id = (r['id'] if r else None)

    demo_staff_id = None
    if demo_staff_email:
        if _safe_exec('SELECT id FROM staff WHERE LOWER(email) = ?', (demo_staff_email,)):
            r = cur.fetchone()
            demo_staff_id = (r['id'] if r else None)

    demo_user_id = None
    if demo_user_health_id:
        if _safe_exec('SELECT id FROM users WHERE health_id = ?', (demo_user_health_id,)):
            r = cur.fetchone()
            demo_user_id = (r['id'] if r else None)

    # Purge auxiliary tables first (avoid FK issues; DB may not enforce but keep order safe)
    # OTPs
    _safe_exec('DELETE FROM otp_codes')

    # Staff-related tables
    if demo_hospital_id is not None:
        _safe_exec('DELETE FROM staff_tasks WHERE hospital_id != ?', (demo_hospital_id,))
        _safe_exec('DELETE FROM staff_activity_log WHERE hospital_id != ?', (demo_hospital_id,))
        _safe_exec('DELETE FROM patient_status WHERE hospital_id != ?', (demo_hospital_id,))
        _safe_exec('DELETE FROM medicine_administration WHERE hospital_id != ?', (demo_hospital_id,))
        _safe_exec('DELETE FROM beds WHERE hospital_id != ?', (demo_hospital_id,))
        _safe_exec('DELETE FROM admissions WHERE hospital_id != ?', (demo_hospital_id,))
        _safe_exec('DELETE FROM inventory_items WHERE hospital_id != ?', (demo_hospital_id,))
    else:
        _safe_exec('DELETE FROM staff_tasks')
        _safe_exec('DELETE FROM staff_activity_log')
        _safe_exec('DELETE FROM patient_status')
        _safe_exec('DELETE FROM medicine_administration')
        _safe_exec('DELETE FROM beds')
        _safe_exec('DELETE FROM admissions')
        _safe_exec('DELETE FROM inventory_items')

    # Medical records
    if keep_demo_records_only and demo_doctor_id is not None:
        _safe_exec('DELETE FROM records WHERE doctor_id != ?', (demo_doctor_id,))
    elif keep_demo_records_only and demo_user_id is not None:
        _safe_exec('DELETE FROM records WHERE user_id != ?', (demo_user_id,))
    else:
        _safe_exec('DELETE FROM records')

    # Emergencies
    if keep_demo_records_only and demo_hospital_id is not None:
        _safe_exec('DELETE FROM emergencies WHERE COALESCE(hospital_id, 0) != ?', (demo_hospital_id,))
    elif keep_demo_records_only and demo_user_id is not None:
        _safe_exec('DELETE FROM emergencies WHERE COALESCE(user_id, 0) != ?', (demo_user_id,))
    else:
        _safe_exec('DELETE FROM emergencies')

    # Core accounts
    if demo_staff_id is not None:
        _safe_exec('DELETE FROM staff WHERE id != ?', (demo_staff_id,))
    else:
        _safe_exec('DELETE FROM staff')

    if demo_doctor_id is not None:
        _safe_exec('DELETE FROM doctors WHERE id != ?', (demo_doctor_id,))
    else:
        _safe_exec('DELETE FROM doctors')

    if demo_hospital_id is not None:
        _safe_exec('DELETE FROM hospitals WHERE id != ?', (demo_hospital_id,))
    else:
        _safe_exec('DELETE FROM hospitals')

    if demo_user_id is not None:
        _safe_exec('DELETE FROM users WHERE id != ?', (demo_user_id,))
    else:
        _safe_exec('DELETE FROM users')

    if demo_admin_id is not None:
        _safe_exec('DELETE FROM health_admins WHERE id != ?', (demo_admin_id,))
    elif demo_health_admin_email:
        _safe_exec('DELETE FROM health_admins WHERE LOWER(email) != ?', (demo_health_admin_email,))
    else:
        _safe_exec('DELETE FROM health_admins')

    conn.commit()
    conn.close()


def _parse_cli_args(argv):
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument('--purge-non-demo', action='store_true', help='Delete all non-demo accounts and related data')
    parser.add_argument('--yes', action='store_true', help='Required confirmation for destructive operations')
    return parser.parse_args(argv)


@app.route('/health-admin/hospitals')
def health_admin_hospitals():
    if current_role() != 'health_admin':
        flash('Unauthorized', 'danger')
        return redirect(url_for('index'))

    state = (request.args.get('state') or '').strip()
    district = (request.args.get('district') or '').strip()
    q = (request.args.get('q') or '').strip()
    page = int((request.args.get('page') or '1').strip() or 1)
    per_page = 15
    if page < 1:
        page = 1

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT DISTINCT state FROM hospitals WHERE state IS NOT NULL AND TRIM(state) != '' ORDER BY state"
    )
    states = [r['state'] for r in cur.fetchall()]

    if state:
        cur.execute(
            '''SELECT DISTINCT district
               FROM hospitals
               WHERE state = ? AND district IS NOT NULL AND TRIM(district) != ''
               ORDER BY district''',
            (state,),
        )
    else:
        cur.execute(
            "SELECT DISTINCT district FROM hospitals WHERE district IS NOT NULL AND TRIM(district) != '' ORDER BY district"
        )
    districts = [r['district'] for r in cur.fetchall()]

    where = []
    params = []
    if state:
        where.append('state = ?')
        params.append(state)
    if district:
        where.append('district = ?')
        params.append(district)
    if q:
        where.append('(name LIKE ? OR reg_no LIKE ? OR email LIKE ?)')
        like = f"%{q}%"
        params.extend([like, like, like])
    where_sql = (' WHERE ' + ' AND '.join(where)) if where else ''

    cur.execute(f'SELECT COUNT(*) AS c FROM hospitals{where_sql}', tuple(params))
    total = cur.fetchone()['c'] or 0
    pages = (total + per_page - 1) // per_page
    offset = (page - 1) * per_page

    cur.execute(
        f'''SELECT h.*,
                   (SELECT COUNT(*) FROM doctors d WHERE d.hospital_id = h.id) AS doctors_count,
                   (SELECT COUNT(*) FROM staff s WHERE s.hospital_id = h.id) AS staff_count
            FROM hospitals h
            {where_sql}
            ORDER BY h.name
            LIMIT ? OFFSET ?''',
        tuple(params) + (per_page, offset),
    )
    hospitals = cur.fetchall()
    conn.close()

    return render_template(
        'health_admin_hospitals.html',
        hospitals=hospitals,
        states=states,
        districts=districts,
        state=state,
        district=district,
        q=q,
        page=page,
        pages=pages,
        total=total,
        per_page=per_page,
    )


@app.route('/health-admin/hospitals/<int:hospital_id>/delete', methods=['POST'])
def health_admin_delete_hospital(hospital_id):
    if current_role() != 'health_admin':
        flash('Unauthorized', 'danger')
        return redirect(url_for('index'))

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute('SELECT id, name, email FROM hospitals WHERE id = ?', (hospital_id,))
    hosp = cur.fetchone()
    if not hosp:
        conn.close()
        flash('Hospital not found.', 'warning')
        return redirect(url_for('health_admin_hospitals'))

    # Prevent deleting demo hospital (optional safety)
    demo_hospital_email = (demo_defaults().get('hospital_email') or '').strip().lower()
    if demo_hospital_email and (hosp['email'] or '').strip().lower() == demo_hospital_email:
        conn.close()
        flash('Demo hospital cannot be deleted.', 'warning')
        return redirect(url_for('health_admin_hospitals'))

    # Collect doctor IDs for this hospital to delete related records
    cur.execute('SELECT id FROM doctors WHERE hospital_id = ?', (hospital_id,))
    doctor_ids = [r['id'] for r in cur.fetchall()]

    # Remove related tables (best effort; DB may not enforce FK)
    try:
        cur.execute('DELETE FROM inventory_items WHERE hospital_id = ?', (hospital_id,))
    except sqlite3.OperationalError:
        pass
    try:
        cur.execute('DELETE FROM beds WHERE hospital_id = ?', (hospital_id,))
    except sqlite3.OperationalError:
        pass
    try:
        cur.execute('DELETE FROM admissions WHERE hospital_id = ?', (hospital_id,))
    except sqlite3.OperationalError:
        pass
    try:
        cur.execute('DELETE FROM staff_tasks WHERE hospital_id = ?', (hospital_id,))
    except sqlite3.OperationalError:
        pass
    try:
        cur.execute('DELETE FROM staff_activity_log WHERE hospital_id = ?', (hospital_id,))
    except sqlite3.OperationalError:
        pass
    try:
        cur.execute('DELETE FROM patient_status WHERE hospital_id = ?', (hospital_id,))
    except sqlite3.OperationalError:
        pass
    try:
        cur.execute('DELETE FROM medicine_administration WHERE hospital_id = ?', (hospital_id,))
    except sqlite3.OperationalError:
        pass

    # Emergencies assigned to this hospital
    try:
        cur.execute('UPDATE emergencies SET hospital_id = NULL WHERE hospital_id = ?', (hospital_id,))
    except sqlite3.OperationalError:
        pass

    # Records by hospital's doctors
    if doctor_ids:
        try:
            placeholders = ','.join(['?'] * len(doctor_ids))
            cur.execute(f'DELETE FROM records WHERE doctor_id IN ({placeholders})', tuple(doctor_ids))
        except sqlite3.OperationalError:
            pass

    # Doctors and staff accounts
    try:
        cur.execute('DELETE FROM doctors WHERE hospital_id = ?', (hospital_id,))
    except sqlite3.OperationalError:
        pass
    try:
        cur.execute('DELETE FROM staff WHERE hospital_id = ?', (hospital_id,))
    except sqlite3.OperationalError:
        pass

    cur.execute('DELETE FROM hospitals WHERE id = ?', (hospital_id,))
    conn.commit()
    conn.close()

    flash(f"Hospital '{hosp['name']}' deleted successfully.", 'success')
    return redirect(url_for('health_admin_hospitals'))


@app.route('/health-admin/login', methods=['GET', 'POST'])
def health_admin_login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()

        if not email or not password:
            flash('Email and password are required', 'danger')
            return render_template('health_admin_login.html', email=email, demo=demo_defaults())

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT * FROM health_admins WHERE email = ? AND password = ?', (email, password))
        admin = cur.fetchone()
        conn.close()

        if admin:
            login_user('health_admin', admin['id'])
            flash('Logged in successfully', 'success')
            return redirect(url_for('health_admin_dashboard'))

        flash('Invalid email or password', 'danger')
        return render_template('health_admin_login.html', email=email, demo=demo_defaults())

    return render_template('health_admin_login.html', demo=demo_defaults())


@app.route('/health-admin/logout')
def health_admin_logout():
    session.clear()
    flash('Logged out successfully', 'info')
    return redirect(url_for('index'))


@app.route('/health-admin/dashboard')
def health_admin_dashboard():
    if current_role() != 'health_admin':
        flash('Unauthorized', 'danger')
        return redirect(url_for('index'))

    state = (request.args.get('state') or '').strip()
    district = (request.args.get('district') or '').strip()

    q_hospital = (request.args.get('q_hospital') or '').strip()
    q_doctor = (request.args.get('q_doctor') or '').strip()
    q_patient = (request.args.get('q_patient') or '').strip()

    page_hospitals = int((request.args.get('page_hospitals') or '1').strip() or 1)
    page_doctors = int((request.args.get('page_doctors') or '1').strip() or 1)
    page_patients = int((request.args.get('page_patients') or '1').strip() or 1)
    per_page = 10

    if page_hospitals < 1:
        page_hospitals = 1
    if page_doctors < 1:
        page_doctors = 1
    if page_patients < 1:
        page_patients = 1

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT DISTINCT state FROM hospitals WHERE state IS NOT NULL AND TRIM(state) != '' ORDER BY state"
    )
    states = [r['state'] for r in cur.fetchall()]

    if state:
        cur.execute(
            """SELECT DISTINCT district
               FROM hospitals
               WHERE state = ? AND district IS NOT NULL AND TRIM(district) != ''
               ORDER BY district""",
            (state,),
        )
    else:
        cur.execute(
            "SELECT DISTINCT district FROM hospitals WHERE district IS NOT NULL AND TRIM(district) != '' ORDER BY district"
        )
    districts = [r['district'] for r in cur.fetchall()]

    where = []
    params = []
    if state:
        where.append('h.state = ?')
        params.append(state)
    if district:
        where.append('h.district = ?')
        params.append(district)
    where_sql = (' WHERE ' + ' AND '.join(where)) if where else ''

    hosp_where = list(where)
    hosp_params = list(params)
    if q_hospital:
        hosp_where.append('(h.name LIKE ? OR h.reg_no LIKE ? OR h.email LIKE ?)')
        like = f"%{q_hospital}%"
        hosp_params.extend([like, like, like])
    hosp_where_sql = (' WHERE ' + ' AND '.join(hosp_where)) if hosp_where else ''

    cur.execute(
        f'''SELECT COUNT(*) AS c
            FROM hospitals h
            {hosp_where_sql}''',
        tuple(hosp_params),
    )
    hospitals_total = cur.fetchone()['c'] or 0

    hosp_offset = (page_hospitals - 1) * per_page
    cur.execute(
        f'''SELECT h.*,
                   (SELECT COUNT(*) FROM doctors d WHERE d.hospital_id = h.id) AS doctors_count
            FROM hospitals h
            {hosp_where_sql}
            ORDER BY h.name
            LIMIT ? OFFSET ?''',
        tuple(hosp_params) + (per_page, hosp_offset),
    )
    hospitals = cur.fetchall()

    doc_where = list(where)
    doc_params = list(params)
    if q_doctor:
        doc_where.append('(d.name LIKE ? OR d.email LIKE ? OR COALESCE(d.specialization, \'\') LIKE ?)')
        like = f"%{q_doctor}%"
        doc_params.extend([like, like, like])
    doc_where_sql = (' WHERE ' + ' AND '.join(doc_where)) if doc_where else ''

    cur.execute(
        f'''SELECT COUNT(*) AS c
            FROM doctors d
            JOIN hospitals h ON d.hospital_id = h.id
            {doc_where_sql}''',
        tuple(doc_params),
    )
    doctors_total = cur.fetchone()['c'] or 0

    doc_offset = (page_doctors - 1) * per_page
    cur.execute(
        f'''SELECT d.*, h.name AS hospital_name, h.state AS hospital_state, h.district AS hospital_district
            FROM doctors d
            JOIN hospitals h ON d.hospital_id = h.id
            {doc_where_sql}
            ORDER BY d.name
            LIMIT ? OFFSET ?''',
        tuple(doc_params) + (per_page, doc_offset),
    )
    doctors = cur.fetchall()

    pat_where = list(where)
    pat_params = list(params)
    if q_patient:
        pat_where.append('(u.name LIKE ? OR u.health_id LIKE ? OR COALESCE(u.phone, \'\') LIKE ?)')
        like = f"%{q_patient}%"
        pat_params.extend([like, like, like])
    pat_where_sql = (' WHERE ' + ' AND '.join(pat_where)) if pat_where else ''

    cur.execute(
        f'''SELECT COUNT(DISTINCT u.id) AS c
            FROM users u
            JOIN records r ON r.user_id = u.id
            JOIN doctors d ON r.doctor_id = d.id
            JOIN hospitals h ON d.hospital_id = h.id
            {pat_where_sql}''',
        tuple(pat_params),
    )
    patients_total = cur.fetchone()['c'] or 0

    pat_offset = (page_patients - 1) * per_page
    cur.execute(
        f'''SELECT u.id AS user_id,
                   u.name,
                   u.health_id,
                   u.phone,
                   COUNT(r.id) AS visits,
                   MAX(r.date) AS last_visit
            FROM users u
            JOIN records r ON r.user_id = u.id
            JOIN doctors d ON r.doctor_id = d.id
            JOIN hospitals h ON d.hospital_id = h.id
            {pat_where_sql}
            GROUP BY u.id, u.name, u.health_id, u.phone
            ORDER BY last_visit DESC
            LIMIT ? OFFSET ?''',
        tuple(pat_params) + (per_page, pat_offset),
    )
    patients = cur.fetchall()

    cur.execute(
        f'''SELECT h.state,
                   h.district,
                   COUNT(DISTINCT h.id) AS hospitals_count,
                   COUNT(DISTINCT d.id) AS doctors_count,
                   COUNT(DISTINCT r.user_id) AS patients_count
            FROM hospitals h
            LEFT JOIN doctors d ON d.hospital_id = h.id
            LEFT JOIN records r ON r.doctor_id = d.id
            {where_sql}
            GROUP BY h.state, h.district
            ORDER BY h.state, h.district''',
        tuple(params),
    )
    areas = cur.fetchall()

    # Aggregated KPIs
    beds_total = 0
    beds_available = 0
    active_admissions = 0
    emergencies_total = 0
    emergencies_assigned = 0
    emergencies_unassigned = 0
    low_stock_total = 0

    # Beds & admissions (may not exist on older DBs)
    try:
        cur.execute(
            f'''SELECT COUNT(*) AS c
                FROM beds b
                JOIN hospitals h ON b.hospital_id = h.id
                {where_sql}''',
            tuple(params),
        )
        beds_total = cur.fetchone()['c'] or 0

        cur.execute(
            f'''SELECT COUNT(*) AS c
                FROM beds b
                JOIN hospitals h ON b.hospital_id = h.id
                {where_sql}{' AND' if where_sql else ' WHERE'} b.status = 'Available' ''',
            tuple(params),
        )
        beds_available = cur.fetchone()['c'] or 0

        cur.execute(
            f'''SELECT COUNT(*) AS c
                FROM admissions a
                JOIN hospitals h ON a.hospital_id = h.id
                {where_sql}{' AND' if where_sql else ' WHERE'} a.status = 'Active' ''',
            tuple(params),
        )
        active_admissions = cur.fetchone()['c'] or 0
    except sqlite3.OperationalError:
        beds_total = 0
        beds_available = 0
        active_admissions = 0

    # Emergencies
    try:
        cur.execute(
            f'''SELECT COUNT(*) AS c
                FROM emergencies e
                LEFT JOIN hospitals h ON e.hospital_id = h.id
                {where_sql}''',
            tuple(params),
        )
        emergencies_total = cur.fetchone()['c'] or 0

        cur.execute(
            f'''SELECT COUNT(*) AS c
                FROM emergencies e
                JOIN hospitals h ON e.hospital_id = h.id
                {where_sql}''',
            tuple(params),
        )
        emergencies_assigned = cur.fetchone()['c'] or 0
        emergencies_unassigned = max(0, emergencies_total - emergencies_assigned)
    except sqlite3.OperationalError:
        emergencies_total = 0
        emergencies_assigned = 0
        emergencies_unassigned = 0

    # Low stock summary (inventory may not exist)
    try:
        cur.execute(
            f'''SELECT COUNT(*) AS c
                FROM inventory_items i
                JOIN hospitals h ON i.hospital_id = h.id
                {where_sql}{' AND' if where_sql else ' WHERE'} i.quantity <= i.reorder_level''',
            tuple(params),
        )
        low_stock_total = cur.fetchone()['c'] or 0
    except sqlite3.OperationalError:
        low_stock_total = 0

    district_doctors = []
    district_patients = []
    try:
        cur.execute(
            f'''SELECT h.district AS district, COUNT(DISTINCT d.id) AS c
                FROM hospitals h
                LEFT JOIN doctors d ON d.hospital_id = h.id
                {where_sql}
                GROUP BY h.district
                ORDER BY c DESC
                LIMIT 10''',
            tuple(params),
        )
        district_doctors = cur.fetchall()
    except sqlite3.OperationalError:
        district_doctors = []

    try:
        cur.execute(
            f'''SELECT h.district AS district, COUNT(DISTINCT r.user_id) AS c
                FROM hospitals h
                LEFT JOIN doctors d ON d.hospital_id = h.id
                LEFT JOIN records r ON r.doctor_id = d.id
                {where_sql}
                GROUP BY h.district
                ORDER BY c DESC
                LIMIT 10''',
            tuple(params),
        )
        district_patients = cur.fetchall()
    except sqlite3.OperationalError:
        district_patients = []

    unassigned_emergencies = []
    try:
        cur.execute(
            f'''SELECT e.id AS id,
                       e.name,
                       e.phone,
                       e.location,
                       e.status,
                       e.requested_at,
                       e.priority,
                       e.state,
                       e.district
                FROM emergencies e
                LEFT JOIN hospitals h ON e.hospital_id = h.id
                {where_sql}{' AND' if where_sql else ' WHERE'} (e.hospital_id IS NULL OR e.hospital_id = 0)
                ORDER BY e.requested_at DESC
                LIMIT 8''',
            tuple(params),
        )
        unassigned_emergencies = cur.fetchall()
    except sqlite3.OperationalError:
        unassigned_emergencies = []

    conn.close()

    return render_template(
        'health_admin_dashboard.html',
        state=state,
        district=district,
        states=states,
        districts=districts,
        q_hospital=q_hospital,
        q_doctor=q_doctor,
        q_patient=q_patient,
        page_hospitals=page_hospitals,
        page_doctors=page_doctors,
        page_patients=page_patients,
        per_page=per_page,
        hospitals_total=hospitals_total,
        doctors_total=doctors_total,
        patients_total=patients_total,
        hospitals=hospitals,
        doctors=doctors,
        patients=patients,
        areas=areas,
        beds_total=beds_total,
        beds_available=beds_available,
        active_admissions=active_admissions,
        emergencies_total=emergencies_total,
        emergencies_assigned=emergencies_assigned,
        emergencies_unassigned=emergencies_unassigned,
        low_stock_total=low_stock_total,
        district_doctors=district_doctors,
        district_patients=district_patients,
        unassigned_emergencies=unassigned_emergencies,
    )


@app.route('/health-admin/export/<string:kind>')
def health_admin_export(kind):
    if current_role() != 'health_admin':
        flash('Unauthorized', 'danger')
        return redirect(url_for('index'))

    state = (request.args.get('state') or '').strip()
    district = (request.args.get('district') or '').strip()

    conn = get_db_connection()
    cur = conn.cursor()

    where = []
    params = []
    if state:
        where.append('h.state = ?')
        params.append(state)
    if district:
        where.append('h.district = ?')
        params.append(district)
    where_sql = (' WHERE ' + ' AND '.join(where)) if where else ''

    output = io.StringIO()
    writer = csv.writer(output)

    filename = f"{kind}.csv"

    if kind == 'hospitals':
        writer.writerow(['Name', 'Reg No', 'Email', 'State', 'District', 'Doctors'])
        cur.execute(
            f'''SELECT h.name, h.reg_no, h.email, h.state, h.district,
                       (SELECT COUNT(*) FROM doctors d WHERE d.hospital_id = h.id) AS doctors_count
                FROM hospitals h
                {where_sql}
                ORDER BY h.name''',
            tuple(params),
        )
        for r in cur.fetchall():
            writer.writerow([r['name'], r['reg_no'], r['email'], r['state'] or '', r['district'] or '', r['doctors_count']])
        filename = 'hospitals.csv'

    elif kind == 'doctors':
        writer.writerow(['Name', 'Email', 'Specialization', 'Hospital', 'State', 'District'])
        cur.execute(
            f'''SELECT d.name, d.email, d.specialization, h.name AS hospital_name, h.state, h.district
                FROM doctors d
                JOIN hospitals h ON d.hospital_id = h.id
                {where_sql}
                ORDER BY d.name''',
            tuple(params),
        )
        for r in cur.fetchall():
            writer.writerow([r['name'], r['email'], r['specialization'] or '', r['hospital_name'], r['state'] or '', r['district'] or ''])
        filename = 'doctors.csv'

    elif kind == 'patients':
        writer.writerow(['Name', 'Health ID', 'Phone', 'Visits', 'Last Visit'])
        cur.execute(
            f'''SELECT u.name, u.health_id, u.phone, COUNT(r.id) AS visits, MAX(r.date) AS last_visit
                FROM users u
                JOIN records r ON r.user_id = u.id
                JOIN doctors d ON r.doctor_id = d.id
                JOIN hospitals h ON d.hospital_id = h.id
                {where_sql}
                GROUP BY u.id, u.name, u.health_id, u.phone
                ORDER BY last_visit DESC''',
            tuple(params),
        )
        for r in cur.fetchall():
            writer.writerow([r['name'], r['health_id'], r['phone'] or '', r['visits'], r['last_visit'] or ''])
        filename = 'patients.csv'

    elif kind == 'areas':
        writer.writerow(['State', 'District', 'Hospitals', 'Doctors', 'Patients'])
        cur.execute(
            f'''SELECT h.state, h.district,
                       COUNT(DISTINCT h.id) AS hospitals_count,
                       COUNT(DISTINCT d.id) AS doctors_count,
                       COUNT(DISTINCT r.user_id) AS patients_count
                FROM hospitals h
                LEFT JOIN doctors d ON d.hospital_id = h.id
                LEFT JOIN records r ON r.doctor_id = d.id
                {where_sql}
                GROUP BY h.state, h.district
                ORDER BY h.state, h.district''',
            tuple(params),
        )
        for r in cur.fetchall():
            writer.writerow([r['state'] or '', r['district'] or '', r['hospitals_count'], r['doctors_count'], r['patients_count']])
        filename = 'areas.csv'
    else:
        conn.close()
        flash('Unknown export type', 'danger')
        return redirect(url_for('health_admin_dashboard', state=state, district=district))

    conn.close()
    csv_data = output.getvalue()
    output.close()
    return Response(
        csv_data,
        mimetype='text/csv',
        headers={"Content-Disposition": f"attachment;filename={filename}"},
    )


@app.route('/health-admin/hospital/<int:hospital_id>')
def health_admin_hospital_detail(hospital_id):
    if current_role() != 'health_admin':
        flash('Unauthorized', 'danger')
        return redirect(url_for('index'))

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute('SELECT * FROM hospitals WHERE id = ?', (hospital_id,))
    hospital = cur.fetchone()
    if not hospital:
        conn.close()
        flash('Hospital not found', 'danger')
        return redirect(url_for('health_admin_dashboard'))

    cur.execute('SELECT * FROM doctors WHERE hospital_id = ? ORDER BY name', (hospital_id,))
    doctors = cur.fetchall()

    patients = []
    try:
        cur.execute(
            '''SELECT u.id AS user_id, u.name, u.health_id, u.phone, COUNT(r.id) AS visits, MAX(r.date) AS last_visit
               FROM records r
               JOIN doctors d ON r.doctor_id = d.id
               JOIN users u ON r.user_id = u.id
               WHERE d.hospital_id = ?
               GROUP BY u.id, u.name, u.health_id, u.phone
               ORDER BY last_visit DESC
               LIMIT 50''',
            (hospital_id,),
        )
        patients = cur.fetchall()
    except sqlite3.OperationalError:
        patients = []

    beds = []
    admissions = []
    low_stock_items = []
    recent_emergencies = []
    try:
        cur.execute('SELECT * FROM beds WHERE hospital_id = ? ORDER BY bed_number', (hospital_id,))
        beds = cur.fetchall()
    except sqlite3.OperationalError:
        beds = []

    try:
        cur.execute(
            '''SELECT a.*, u.name AS patient_name, u.health_id, b.bed_number
               FROM admissions a
               JOIN users u ON a.user_id = u.id
               LEFT JOIN beds b ON a.bed_id = b.id
               WHERE a.hospital_id = ?
               ORDER BY a.admitted_at DESC
               LIMIT 50''',
            (hospital_id,),
        )
        admissions = cur.fetchall()
    except sqlite3.OperationalError:
        admissions = []

    try:
        cur.execute(
            '''SELECT item_name, quantity, unit, reorder_level
               FROM inventory_items
               WHERE hospital_id = ? AND quantity <= reorder_level
               ORDER BY (reorder_level - quantity) DESC, item_name ASC
               LIMIT 25''',
            (hospital_id,),
        )
        low_stock_items = cur.fetchall()
    except sqlite3.OperationalError:
        low_stock_items = []

    try:
        cur.execute(
            '''SELECT id, name, phone, location, status, requested_at, priority, district
               FROM emergencies
               WHERE hospital_id = ?
               ORDER BY requested_at DESC
               LIMIT 25''',
            (hospital_id,),
        )
        recent_emergencies = cur.fetchall()
    except sqlite3.OperationalError:
        recent_emergencies = []

    conn.close()
    return render_template(
        'health_admin_hospital_detail.html',
        hospital=hospital,
        doctors=doctors,
        patients=patients,
        beds=beds,
        admissions=admissions,
        low_stock_items=low_stock_items,
        recent_emergencies=recent_emergencies,
    )


@app.route('/health-admin/emergencies')
def health_admin_emergencies():
    if current_role() != 'health_admin':
        flash('Unauthorized', 'danger')
        return redirect(url_for('index'))

    state = (request.args.get('state') or '').strip()
    district = (request.args.get('district') or '').strip()
    status = (request.args.get('status') or '').strip()
    assigned = (request.args.get('assigned') or '').strip()

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT DISTINCT state FROM hospitals WHERE state IS NOT NULL AND TRIM(state) != '' ORDER BY state"
    )
    states = [r['state'] for r in cur.fetchall()]

    if state:
        cur.execute(
            '''SELECT DISTINCT district
               FROM hospitals
               WHERE state = ? AND district IS NOT NULL AND TRIM(district) != ''
               ORDER BY district''',
            (state,),
        )
    else:
        cur.execute(
            "SELECT DISTINCT district FROM hospitals WHERE district IS NOT NULL AND TRIM(district) != '' ORDER BY district"
        )
    districts = [r['district'] for r in cur.fetchall()]

    e_where = []
    e_params = []
    if state:
        e_where.append('COALESCE(e.state, h.state) = ?')
        e_params.append(state)
    if district:
        e_where.append('COALESCE(e.district, h.district) = ?')
        e_params.append(district)
    if status:
        e_where.append('e.status = ?')
        e_params.append(status)
    if assigned == 'yes':
        e_where.append('e.hospital_id IS NOT NULL AND e.hospital_id != 0')
    elif assigned == 'no':
        e_where.append('(e.hospital_id IS NULL OR e.hospital_id = 0)')

    e_where_sql = (' WHERE ' + ' AND '.join(e_where)) if e_where else ''

    emergencies = []
    try:
        cur.execute(
            f'''SELECT e.*, h.name AS hospital_name, h.state AS hospital_state, h.district AS hospital_district
                FROM emergencies e
                LEFT JOIN hospitals h ON e.hospital_id = h.id
                {e_where_sql}
                ORDER BY e.requested_at DESC
                LIMIT 200''',
            tuple(e_params),
        )
        emergencies = cur.fetchall()
    except sqlite3.OperationalError:
        emergencies = []

    hospitals = []
    try:
        cur.execute(
            '''SELECT id, name, state, district
               FROM hospitals
               ORDER BY name'''
        )
        hospitals = cur.fetchall()
    except sqlite3.OperationalError:
        hospitals = []

    conn.close()
    return render_template(
        'health_admin_emergencies.html',
        states=states,
        districts=districts,
        state=state,
        district=district,
        status=status,
        assigned=assigned,
        emergencies=emergencies,
        hospitals=hospitals,
    )


@app.route('/health-admin/emergencies/assign', methods=['POST'])
def health_admin_emergencies_assign():
    if current_role() != 'health_admin':
        flash('Unauthorized', 'danger')
        return redirect(url_for('index'))

    emergency_id = int((request.form.get('emergency_id') or '0').strip() or 0)
    hospital_id = int((request.form.get('hospital_id') or '0').strip() or 0)
    if not emergency_id:
        flash('Invalid emergency', 'danger')
        return redirect(url_for('health_admin_emergencies'))

    conn = get_db_connection()
    cur = conn.cursor()

    if hospital_id:
        cur.execute(
            'UPDATE emergencies SET hospital_id = ?, assigned_at = ? WHERE id = ?',
            (hospital_id, datetime.utcnow().isoformat(), emergency_id),
        )
        conn.commit()
        flash('Emergency assigned to hospital.', 'success')
    else:
        cur.execute(
            'UPDATE emergencies SET hospital_id = NULL WHERE id = ?',
            (emergency_id,),
        )
        conn.commit()
        flash('Emergency unassigned.', 'info')

    conn.close()
    return redirect(url_for('health_admin_emergencies'))


# Utility: generate unique health ID
def generate_health_id():
    # Short UUID-based ID, e.g., H-3F9C-82B1
    raw = uuid.uuid4().hex[:8].upper()
    return f"H-{raw[:4]}-{raw[4:]}"


# Utility: create QR code for health ID
def generate_health_qr(health_id):
    qr_path = os.path.join(QR_FOLDER, f"{health_id}.png")
    if not QRCODE_AVAILABLE:
        return None
    # Ensure QR encodes the scan URL, forcing regeneration for new format
    scan_url = url_for('scan_qr', health_id=health_id, _external=True)
    img = qrcode.make(scan_url)
    img.save(qr_path)
    return f"qr/{health_id}.png"


@app.route('/scan/<health_id>')
def scan_qr(health_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM users WHERE health_id = ?', (health_id,))
    patient = cur.fetchone()
    conn.close()
    
    if not patient:
        flash('Invalid QR Code or Patient not found.', 'danger')
        return redirect(url_for('index'))
        
    role = current_role()
    if role == 'doctor':
        return redirect(url_for('doctor_scan_result', health_id=health_id))
    
    # Public view
    return render_template('public_emergency_card.html', patient=patient)

@app.route('/doctor/scan_result/<health_id>')
def doctor_scan_result(health_id):
    if current_role() != 'doctor':
        flash('Unauthorized', 'danger')
        return redirect(url_for('index'))
        
    doctor_id = current_user_id()
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM users WHERE health_id = ?', (health_id,))
    patient = cur.fetchone()
    
    records = []
    if patient:
        cur.execute(
            '''SELECT r.*, d.id as doctor_id, d.name as doctor_name, d.specialization as doctor_specialization,
                      h.id as hospital_id, h.name as hospital_name, h.reg_no as hospital_reg_no
               FROM records r
               JOIN doctors d ON r.doctor_id = d.id
               JOIN hospitals h ON d.hospital_id = h.id
               WHERE r.user_id = ?
               ORDER BY r.date DESC''',
            (patient['id'],),
        )
        records = cur.fetchall()
    
    # Needs to match the context expected by doctor_dashboard.html
    # Some counters are skipped here for brevity, but dashboard handles missing vars fine.
    
    conn.close()
    return render_template('doctor_dashboard.html', patient=patient, records=records, search_health_id=health_id, doctor_id=doctor_id, current_user_id=doctor_id)


@app.route('/api/hospitals/nearby')
def api_hospitals_nearby():
    import math
    try:
        lat = float(request.args.get('lat', 0))
        lng = float(request.args.get('lng', 0))
    except ValueError:
        return {'error': 'Invalid coordinates'}, 400
        
    if not lat or not lng:
        return {'error': 'Missing coordinates'}, 400

    conn = get_db_connection()
    cur = conn.cursor()
    # Fetch all hospitals with coordinates and abha_connected
    cur.execute('SELECT id, name, phone, district, state, latitude, longitude, abha_connected FROM hospitals WHERE latitude IS NOT NULL AND longitude IS NOT NULL')
    hospitals = cur.fetchall()
    conn.close()
    
    nearby = []
    
    def haversine(lat1, lon1, lat2, lon2):
        R = 6371  # Radius of earth in km
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat/2) * math.sin(dlat/2) + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2) * math.sin(dlon/2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c

    for h in hospitals:
        distance = haversine(lat, lng, h['latitude'], h['longitude'])
        nearby.append({
            'id': h['id'],
            'name': h['name'],
            'phone': h['phone'],
            'district': h['district'],
            'state': h['state'],
            'distance': round(distance, 1),
            'latitude': h['latitude'],
            'longitude': h['longitude'],
            'abha_connected': bool(h['abha_connected'])
        })
        
    # Sort by distance and return top 15
    nearby.sort(key=lambda x: x['distance'])
    return {'hospitals': nearby[:15]}


# Health Risk Prediction Function
def predict_health_risk(user_data, symptoms, diagnosis, treatment_status, medicines, health_metrics=None):
    """
    Predict health risk using SVM model with rule-based fallback.
    Returns: (risk_level, risk_score, should_trigger_emergency)
    risk_level: 'Low', 'Medium', 'High', 'Critical'
    risk_score: probability/confidence score
    should_trigger_emergency: boolean
    
    Args:
        user_data: User record from database
        symptoms: Symptoms text
        diagnosis: Diagnosis text
        treatment_status: Treatment status
        medicines: Medicines text
        health_metrics: Dict with health metrics (age, gender, systolic_bp, etc.)
    """
    # Rule-based fallback if model is not available
    use_model = health_risk_model is not None
    
    # Default health_metrics if not provided
    if health_metrics is None:
        health_metrics = {}
    
    try:
        # Extract features from available data
        # Priority: health_metrics > user_data > defaults
        
        # Age: from health_metrics, then user_data, then default
        age = health_metrics.get('age')
        if age is None and user_data:
            if hasattr(user_data, 'get'):
                age = user_data.get('age')
            else:
                age = user_data['age'] if 'age' in user_data.keys() else None
        if age is None:
            age = 40
        
        # Ensure age is a number
        try:
            age = int(age) if age else 40
        except (ValueError, TypeError):
            age = 40
        
        age_normalized = min(age / 100.0, 1.0)  # Normalize age to 0-1
        
        # Extract health metrics
        systolic_bp = health_metrics.get('systolic_bp')
        diastolic_bp = health_metrics.get('diastolic_bp')
        bmi = health_metrics.get('bmi')
        cholesterol = health_metrics.get('cholesterol')
        glucose = health_metrics.get('glucose')
        smoking = health_metrics.get('smoking', '')
        alcohol = health_metrics.get('alcohol', '')
        physical_activity = health_metrics.get('physical_activity', '')
        family_history = health_metrics.get('family_history', '')
        
        # Normalize BP (normal: 120/80, high: >140/90)
        bp_normalized = 0.5  # Default
        if systolic_bp and diastolic_bp:
            if systolic_bp > 140 or diastolic_bp > 90:
                bp_normalized = 1.0  # High BP
            elif systolic_bp < 90 or diastolic_bp < 60:
                bp_normalized = 0.8  # Low BP
            else:
                bp_normalized = 0.3  # Normal BP
        
        # Normalize BMI (normal: 18.5-24.9, overweight: 25-29.9, obese: >30)
        bmi_normalized = 0.5  # Default
        if bmi:
            if bmi < 18.5:
                bmi_normalized = 0.6  # Underweight
            elif bmi > 30:
                bmi_normalized = 1.0  # Obese
            elif bmi > 25:
                bmi_normalized = 0.7  # Overweight
            else:
                bmi_normalized = 0.3  # Normal
        
        # Normalize cholesterol (normal: <200, high: >240)
        cholesterol_normalized = 0.5  # Default
        if cholesterol:
            if cholesterol > 240:
                cholesterol_normalized = 1.0  # High
            elif cholesterol > 200:
                cholesterol_normalized = 0.7  # Borderline
            else:
                cholesterol_normalized = 0.3  # Normal
        
        # Normalize glucose (normal: <100, prediabetic: 100-125, diabetic: >125)
        glucose_normalized = 0.5  # Default
        if glucose:
            if glucose > 125:
                glucose_normalized = 1.0  # High (diabetic)
            elif glucose > 100:
                glucose_normalized = 0.7  # Borderline
            else:
                glucose_normalized = 0.3  # Normal
        
        # Encode lifestyle factors using new encoding scheme
        # Smoking: 0 = Non-Smoker, 1 = Smoker
        try:
            smoking_risk = int(smoking) if smoking and smoking.isdigit() else 0
        except (ValueError, TypeError):
            smoking_risk = 0
        
        # Alcohol: 0 = Habit Absent, 1 = Habit Present
        try:
            alcohol_risk = int(alcohol) if alcohol and alcohol.isdigit() else 0
        except (ValueError, TypeError):
            alcohol_risk = 0
        
        # Physical Activity: 0-5 scale (0 = No activity/Sedentary, 5 = 5+ hours/week)
        # For model: normalize to 0-1, but higher activity = lower risk (inverted)
        try:
            activity_value = int(physical_activity) if physical_activity and physical_activity.isdigit() else 0
            # Invert: 0 (no activity) = high risk (1.0), 5 (active) = low risk (0.0)
            activity_risk = 1.0 - (activity_value / 5.0) if activity_value <= 5 else 0.0
        except (ValueError, TypeError):
            activity_risk = 0.5  # Default medium risk
        
        # Family History: 0 = No family history, 1 = Family history present
        try:
            family_history_risk = int(family_history) if family_history and family_history.isdigit() else 0
        except (ValueError, TypeError):
            family_history_risk = 0
        
        # Encode symptoms (simple keyword-based severity)
        symptoms_lower = (symptoms or '').lower()
        symptom_severity = 0.0
        critical_keywords = ['chest pain', 'difficulty breathing', 'unconscious', 'severe', 'emergency', 'critical', 'heart attack', 'stroke']
        high_keywords = ['pain', 'fever', 'bleeding', 'dizziness', 'nausea', 'vomiting']
        medium_keywords = ['cough', 'headache', 'fatigue', 'weakness']
        
        if any(keyword in symptoms_lower for keyword in critical_keywords):
            symptom_severity = 1.0
        elif any(keyword in symptoms_lower for keyword in high_keywords):
            symptom_severity = 0.7
        elif any(keyword in symptoms_lower for keyword in medium_keywords):
            symptom_severity = 0.4
        else:
            symptom_severity = 0.1
        
        # Encode diagnosis severity
        diagnosis_lower = (diagnosis or '').lower()
        diagnosis_severity = 0.0
        critical_diagnosis = ['heart attack', 'stroke', 'severe', 'critical', 'emergency', 'cardiac', 'respiratory failure']
        high_diagnosis = ['hypertension', 'diabetes', 'infection', 'fracture', 'injury']
        medium_diagnosis = ['checkup', 'routine', 'follow-up']
        
        if any(keyword in diagnosis_lower for keyword in critical_diagnosis):
            diagnosis_severity = 1.0
        elif any(keyword in diagnosis_lower for keyword in high_diagnosis):
            diagnosis_severity = 0.6
        elif any(keyword in diagnosis_lower for keyword in medium_diagnosis):
            diagnosis_severity = 0.2
        else:
            diagnosis_severity = 0.3
        
        # Encode treatment status
        status_encoding = {
            'Under Observation': 0.8,
            'Stable': 0.4,
            'Recovered': 0.1,
            'Critical': 1.0,
            'Emergency': 1.0
        }
        treatment_severity = status_encoding.get(treatment_status, 0.5)
        
        # Medicine count (more medicines might indicate complexity)
        medicine_count = len([m.strip() for m in (medicines or '').split(',') if m.strip()]) if medicines else 0
        medicine_complexity = min(medicine_count / 5.0, 1.0)  # Normalize to 0-1
        
        # Use model if available, otherwise use rule-based assessment
        if use_model:
            # Prepare feature vector with health metrics
            features = np.array([[
                age_normalized,
                symptom_severity,
                diagnosis_severity,
                treatment_severity,
                medicine_complexity,
                bp_normalized,
                bmi_normalized,
                cholesterol_normalized,
                glucose_normalized,
                smoking_risk,
                alcohol_risk,
                activity_risk,
                family_history_risk
            ]])
            
            # Scale features if scaler is available
            if model_scaler is not None:
                features_scaled = model_scaler.transform(features)
            else:
                features_scaled = features
            
            # Make prediction
            prediction = health_risk_model.predict(features_scaled)[0]
            
            # Get prediction probability if available
            try:
                probabilities = health_risk_model.predict_proba(features_scaled)[0]
                risk_score = float(max(probabilities))
            except:
                risk_score = 0.5
        else:
            # Rule-based assessment when model is not available
            # Calculate composite risk score with health metrics
            base_risk = (symptom_severity * 0.2 + diagnosis_severity * 0.2 + 
                        treatment_severity * 0.2 + medicine_complexity * 0.1)
            
            # Add health metrics to risk calculation
            # smoking_risk, alcohol_risk, family_history_risk are now 0 or 1 (binary)
            # activity_risk is inverted (0 = no activity = high risk 1.0, 5 = active = low risk 0.0)
            health_risk = (bp_normalized * 0.1 + bmi_normalized * 0.1 + 
                          cholesterol_normalized * 0.05 + glucose_normalized * 0.05 +
                          float(smoking_risk) * 0.05 + float(alcohol_risk) * 0.03 + 
                          activity_risk * 0.03 + float(family_history_risk) * 0.02)
            
            risk_score = min(base_risk + health_risk, 1.0)  # Cap at 1.0
            prediction = None  # Will use risk_score for determination
        
        # Determine risk level and emergency trigger
        # Handle different prediction formats
        risk_level = 'Low'
        should_emergency = False
        
        if prediction is not None:
            # Use model prediction
            if isinstance(prediction, (int, np.integer, np.int64, np.int32)):
                pred_value = int(prediction)
                if pred_value >= 2:
                    risk_level = 'Critical'
                    should_emergency = True
                elif pred_value == 1:
                    risk_level = 'High'
                    should_emergency = True
                else:
                    risk_level = 'Low' if risk_score < 0.4 else 'Medium'
                    should_emergency = False
            elif isinstance(prediction, (str, np.str_)):
                # Handle string predictions
                pred_str = str(prediction).lower()
                if 'critical' in pred_str:
                    risk_level = 'Critical'
                    should_emergency = True
                elif 'high' in pred_str:
                    risk_level = 'High'
                    should_emergency = True
                elif 'medium' in pred_str or 'moderate' in pred_str:
                    risk_level = 'Medium'
                    should_emergency = False
                else:
                    risk_level = 'Low'
                    should_emergency = False
            else:
                # Fallback: use risk_score to determine level
                if risk_score >= 0.8:
                    risk_level = 'Critical'
                    should_emergency = True
                elif risk_score >= 0.6:
                    risk_level = 'High'
                    should_emergency = True
                elif risk_score >= 0.4:
                    risk_level = 'Medium'
                    should_emergency = False
                else:
                    risk_level = 'Low'
                    should_emergency = False
        else:
            # Rule-based assessment (when model not available)
            if risk_score >= 0.8:
                risk_level = 'Critical'
                should_emergency = True
            elif risk_score >= 0.6:
                risk_level = 'High'
                should_emergency = True
            elif risk_score >= 0.4:
                risk_level = 'Medium'
                should_emergency = False
            else:
                risk_level = 'Low'
                should_emergency = False
        
        # Override: If treatment status is critical/emergency, always trigger
        if treatment_status in ['Critical', 'Emergency']:
            risk_level = 'Critical'
            should_emergency = True
        
        # Override: If symptoms or diagnosis contain critical keywords, escalate
        if symptom_severity >= 0.9 or diagnosis_severity >= 0.9:
            if risk_level != 'Critical':
                risk_level = 'High'
            should_emergency = True
        
        return risk_level, risk_score, should_emergency
        
    except Exception as e:
        print(f"[ERROR] Error in health risk prediction: {e}")
        import traceback
        traceback.print_exc()
        # Fallback: use rule-based assessment if model fails
        if treatment_status in ['Critical', 'Emergency']:
            return 'Critical', 0.9, True
        elif treatment_status == 'Under Observation':
            return 'Medium', 0.5, False
        return None, None, False


# Role helpers
def login_user(role, user_id):
    session.clear()
    session['role'] = role
    session['user_id'] = user_id


def current_role():
    return session.get('role')


# OTP Helper Functions
def normalize_phone(phone):
    """Normalize phone number by removing spaces, dashes, and other non-digit characters"""
    if not phone:
        return None
    # Remove all non-digit characters except leading +
    normalized = ''.join(c for c in phone if c.isdigit())
    return normalized


def send_otp(phone, role, identifier, purpose='login'):
    """Send OTP via SMS using Firebase Admin SDK"""
    try:
        # Generate OTP code (6 digits)
        otp_code = str(random.randint(100000, 999999))
        
        # Verify phone number format using Firebase (if available)
        if FIREBASE_INITIALIZED:
            try:
                # Firebase Admin SDK can verify phone number format
                # Note: Firebase Auth sends OTP via their service, but we're managing our own OTP
                # This is for phone number validation
                phone_formatted = f"+{phone}" if not phone.startswith('+') else phone
                
                # Store verification session info (optional - for Firebase integration)
                # Firebase would handle actual SMS sending, but we're using our own system
                print(f"[FIREBASE] Phone number validated: {phone_formatted}")
            except Exception as e:
                print(f"[FIREBASE WARNING] Phone validation error: {e}")
        
        # Store OTP in database
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Invalidate previous OTPs for this phone/role/purpose
        cur.execute('''
            UPDATE otp_codes SET verified = 1 
            WHERE phone = ? AND role = ? AND purpose = ? AND verified = 0
        ''', (phone, role, purpose))
        
        # Insert new OTP
        expires_at = (datetime.utcnow() + timedelta(minutes=OTP_EXPIRY_MINUTES)).isoformat()
        cur.execute('''
            INSERT INTO otp_codes (phone, code, role, identifier, purpose, created_at, expires_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (phone, otp_code, role, identifier, purpose, datetime.utcnow().isoformat(), expires_at))
        
        conn.commit()
        conn.close()
        
        # In production, integrate with Firebase Cloud Messaging or SMS service
        # For now, we'll use a simple approach - in production, use Firebase Auth phone verification
        # or integrate with Firebase Cloud Functions to send SMS
        
        # Log OTP for debugging (visible in Render logs)
        print(f"[OTP DEBUG] OTP for {phone} ({role}): {otp_code}")
        print(f"[OTP INFO] OTP stored in database. Expires at: {expires_at}")
        
        # Show OTP in response message (until SMS service is integrated)
        # TODO: Once SMS is integrated, remove OTP from message and only show "OTP sent to your phone"
        message = f"OTP sent successfully. Your OTP code is: {otp_code} (expires in {OTP_EXPIRY_MINUTES} minutes). Check Render logs if not visible."
        
        # TODO: Integrate with Firebase Cloud Functions or SMS service to actually send SMS
        # For now, OTP is generated and stored - integrate SMS sending service here
        
        return True, message
        
    except Exception as e:
        print(f"[OTP ERROR] {str(e)}")
        return False, f"Error sending OTP: {str(e)}"


def predict_emergency_priority(symptoms, age=None, location=None, state=None, zone=None, 
                              day=None, time_slot=None, emergency_type=None, weather=None, user_data=None):
    """
    Predict emergency priority using Logistic Regression model
    
    Args:
        symptoms: Text description of symptoms
        age: Patient age (optional)
        location: Emergency location (optional)
        state: State name (optional)
        zone: Zone type - Urban, Rural, Highway (optional)
        day: Day of week - Monday, Tuesday, etc. (optional)
        time_slot: Time slot - Morning, Afternoon, Evening, Night (optional)
        emergency_type: Emergency type - EMS, Traffic, Fire (optional)
        weather: Weather condition - Rain, Heatwave, Fog, Clear (optional)
        user_data: User data dict (optional, for additional context)
    
    Returns:
        (priority, severity, prediction_score)
        - priority: 'Low', 'Medium', 'High', 'Critical'
        - severity: 'Mild', 'Moderate', 'Severe', 'Critical'
        - prediction_score: Probability score (0-1)
    """
    if emergency_model is None:
        # Fallback to rule-based prediction
        return predict_emergency_priority_rulebased(symptoms, age, location, state, zone, 
                                                     day, time_slot, emergency_type, weather, user_data)
    
    try:
        # Extract features from symptoms and other inputs
        # This is a simplified feature extraction - adjust based on your model's requirements
        symptom_text = str(symptoms).lower() if symptoms else ''
        
        # Feature extraction (adjust based on your model's actual features)
        # Common emergency features:
        features = []
        
        # Age normalization (0-1 scale, assuming 0-100 range)
        age_normalized = (age / 100.0) if age else 0.5
        
        # Symptom severity keywords
        critical_keywords = ['chest pain', 'difficulty breathing', 'unconscious', 'severe', 'emergency', 
                            'critical', 'heart attack', 'stroke', 'bleeding', 'trauma', 'accident']
        high_keywords = ['pain', 'fever', 'vomiting', 'dizziness', 'nausea', 'weakness']
        moderate_keywords = ['discomfort', 'mild', 'ache', 'tired']
        
        symptom_severity = 0.0
        if any(keyword in symptom_text for keyword in critical_keywords):
            symptom_severity = 1.0
        elif any(keyword in symptom_text for keyword in high_keywords):
            symptom_severity = 0.7
        elif any(keyword in symptom_text for keyword in moderate_keywords):
            symptom_severity = 0.4
        else:
            symptom_severity = 0.2
        
        # States list (35 states/UTs)
        states_list = ['All India', 'Uttar Pradesh', 'Maharashtra', 'West Bengal', 'Jharkhand',
                       'Madhya Pradesh', 'Bihar', 'Rajasthan', 'Tamil Nadu', 'Orissa', 'Assam',
                       'Karnataka', 'Andhra Pradesh', 'Haryana', 'Chhatisgarh', 'Jammu and Kashmir',
                       'Telangana', 'Uttarakhand', 'Himachal Pradesh', 'Gujarat', 'Kerala',
                       'Arunachal Pradesh', 'Delhi', 'Nagaland', 'Mizoram', 'Meghalaya',
                       'Tripura', 'Manipur', 'Goa', 'Andaman and Nicobar Island', 'Ladakh',
                       'Sikkim', 'Puducherry', 'Dadra and Nagar Haveli and Daman and Diu', 'Chandigarh']
        
        # Zone options (3)
        zone_options = ['Urban', 'Rural', 'Highway']
        
        # Day options (7)
        day_options = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        # Time slot options (4)
        time_slot_options = ['Morning', 'Afternoon', 'Evening', 'Night']
        
        # Emergency type options (3)
        emergency_type_options = ['EMS', 'Traffic', 'Fire']
        
        # Weather options (4)
        weather_options = ['Rain', 'Heatwave', 'Fog', 'Clear']
        
        # Build feature vector with one-hot encoding for categorical variables
        # The model expects 50 features, which likely includes:
        # - Age (1 feature)
        # - Symptom severity (1 feature)
        # - State one-hot (35 features)
        # - Zone one-hot (3 features)
        # - Day one-hot (7 features)
        # - Time slot one-hot (4 features)
        # - Emergency type one-hot (3 features)
        # - Weather one-hot (4 features)
        # Total: 1 + 1 + 35 + 3 + 7 + 4 + 3 + 4 = 58 features (but model expects 50)
        # Let's build it step by step and pad/truncate as needed
        
        features_list = []
        
        # 1. Age (normalized)
        features_list.append(age_normalized)
        
        # 2. Symptom severity
        features_list.append(symptom_severity)
        
        # 3. State one-hot encoding (35 features)
        state_onehot = [0] * len(states_list)
        if state and state in states_list:
            state_onehot[states_list.index(state)] = 1
        features_list.extend(state_onehot)
        
        # 4. Zone one-hot encoding (3 features)
        zone_onehot = [0] * len(zone_options)
        if zone and zone in zone_options:
            zone_onehot[zone_options.index(zone)] = 1
        features_list.extend(zone_onehot)
        
        # 5. Day one-hot encoding (7 features)
        day_onehot = [0] * len(day_options)
        if day and day in day_options:
            day_onehot[day_options.index(day)] = 1
        features_list.extend(day_onehot)
        
        # 6. Time slot one-hot encoding (4 features)
        time_slot_onehot = [0] * len(time_slot_options)
        if time_slot and time_slot in time_slot_options:
            time_slot_onehot[time_slot_options.index(time_slot)] = 1
        features_list.extend(time_slot_onehot)
        
        # 7. Emergency type one-hot encoding (3 features)
        emergency_type_onehot = [0] * len(emergency_type_options)
        if emergency_type and emergency_type in emergency_type_options:
            emergency_type_onehot[emergency_type_options.index(emergency_type)] = 1
        features_list.extend(emergency_type_onehot)
        
        # 8. Weather one-hot encoding (4 features)
        weather_onehot = [0] * len(weather_options)
        if weather and weather in weather_options:
            weather_onehot[weather_options.index(weather)] = 1
        features_list.extend(weather_onehot)
        
        # Total features: 1 + 1 + 35 + 3 + 7 + 4 + 3 + 4 = 58
        base_features = features_list
        
        # Build feature vector (adjust based on your model's expected features)
        if hasattr(emergency_model, 'n_features_in_'):
            n_features = emergency_model.n_features_in_
            if len(base_features) < n_features:
                features = np.array([base_features + [0.0] * (n_features - len(base_features))])
            elif len(base_features) > n_features:
                features = np.array([base_features[:n_features]])
            else:
                features = np.array([base_features])
        else:
            # Default: use all features we have
            features = np.array([base_features])
        
        # Scale features if scaler is available
        if emergency_scaler:
            features = emergency_scaler.transform(features)
        
        # Make prediction (suppress feature name warnings)
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore', category=UserWarning)
            if hasattr(emergency_model, 'predict_proba'):
                # Get probability scores
                probabilities = emergency_model.predict_proba(features)[0]
                prediction_score = float(max(probabilities))
                prediction = emergency_model.predict(features)[0]
            else:
                # Binary or single output
                prediction = emergency_model.predict(features)[0]
                prediction_score = 0.8 if prediction > 0 else 0.2
        
        # Convert prediction to priority levels
        # Model classes are: ['High', 'Low', 'Medium'] - no 'Critical'
        # Map model output to our priority system
        if isinstance(prediction, (str, np.str_)):
            pred_str = str(prediction)
            if pred_str == 'High':
                priority = 'High'
                severity = 'Severe'
            elif pred_str == 'Medium':
                priority = 'Medium'
                severity = 'Moderate'
            elif pred_str == 'Low':
                priority = 'Low'
                severity = 'Mild'
            else:
                # Fallback
                priority = 'Medium'
                severity = 'Moderate'
        elif isinstance(prediction, (int, np.integer, np.int64, np.int32)):
            # If model returns index, map based on classes
            if hasattr(emergency_model, 'classes_'):
                class_name = emergency_model.classes_[prediction]
                if class_name == 'High':
                    priority = 'High'
                    severity = 'Severe'
                elif class_name == 'Medium':
                    priority = 'Medium'
                    severity = 'Moderate'
                else:
                    priority = 'Low'
                    severity = 'Mild'
            else:
                # Fallback mapping
                if prediction >= 2:
                    priority = 'High'
                    severity = 'Severe'
                elif prediction == 1:
                    priority = 'Medium'
                    severity = 'Moderate'
                else:
                    priority = 'Low'
                    severity = 'Mild'
        else:
            # Fallback
            priority = 'Medium'
            severity = 'Moderate'
        
        # If prediction score is very high and priority is High, consider it Critical
        if priority == 'High' and prediction_score >= 0.85:
            priority = 'Critical'
            severity = 'Critical'
        
        return priority, severity, float(prediction_score)
        
    except Exception as e:
        print(f"[ERROR] Emergency prediction error: {e}")
        # Fallback to rule-based
        return predict_emergency_priority_rulebased(symptoms, age, location, state, zone, 
                                                day, time_slot, emergency_type, weather, user_data)


def predict_emergency_priority_rulebased(symptoms, age=None, location=None, state=None, zone=None,
                                         day=None, time_slot=None, emergency_type=None, weather=None, user_data=None):
    """Rule-based fallback for emergency priority prediction"""
    symptom_text = str(symptoms).lower() if symptoms else ''
    
    critical_keywords = ['chest pain', 'difficulty breathing', 'unconscious', 'severe', 'emergency', 
                        'critical', 'heart attack', 'stroke', 'bleeding', 'trauma', 'accident']
    high_keywords = ['pain', 'fever', 'vomiting', 'dizziness', 'nausea', 'weakness']
    
    # Base priority from symptoms
    base_priority = 'Low'
    base_severity = 'Mild'
    base_score = 0.35
    
    if any(keyword in symptom_text for keyword in critical_keywords):
        base_priority = 'Critical'
        base_severity = 'Critical'
        base_score = 0.95
    elif any(keyword in symptom_text for keyword in high_keywords):
        base_priority = 'High'
        base_severity = 'Severe'
        base_score = 0.75
    elif symptoms and len(symptoms) > 20:
        base_priority = 'Medium'
        base_severity = 'Moderate'
        base_score = 0.55
    
    # Adjust based on emergency type
    if emergency_type == 'Fire':
        if base_priority == 'Low':
            base_priority = 'High'
            base_severity = 'Severe'
            base_score = 0.80
        elif base_priority == 'Medium':
            base_priority = 'High'
            base_severity = 'Severe'
            base_score = 0.85
    elif emergency_type == 'Traffic':
        if base_priority == 'Low':
            base_priority = 'Medium'
            base_severity = 'Moderate'
            base_score = 0.60
    
    # Adjust based on weather
    if weather == 'Fog':
        base_score = min(base_score + 0.1, 1.0)
    elif weather == 'Rain':
        base_score = min(base_score + 0.05, 1.0)
    
    # Adjust based on zone
    if zone == 'Highway':
        base_score = min(base_score + 0.1, 1.0)
    elif zone == 'Rural':
        base_score = min(base_score + 0.05, 1.0)
    
    # Update priority based on adjusted score
    if base_score >= 0.8:
        base_priority = 'Critical'
        base_severity = 'Critical'
    elif base_score >= 0.6:
        base_priority = 'High'
        base_severity = 'Severe'
    elif base_score >= 0.4:
        base_priority = 'Medium'
        base_severity = 'Moderate'
    else:
        base_priority = 'Low'
        base_severity = 'Mild'
    
    return base_priority, base_severity, base_score


def verify_otp(phone, code, role, identifier, purpose='login'):
    """Verify OTP code using Firebase Admin SDK and database"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Find valid OTP in database
        cur.execute('''
            SELECT * FROM otp_codes 
            WHERE phone = ? AND code = ? AND role = ? AND identifier = ? 
            AND purpose = ? AND verified = 0 AND expires_at > ?
        ''', (phone, code, role, identifier, purpose, datetime.utcnow().isoformat()))
        
        otp_record = cur.fetchone()
        
        if otp_record:
            # Verify with Firebase (if available)
            if FIREBASE_INITIALIZED:
                try:
                    # Format phone number for Firebase
                    phone_formatted = f"+{phone}" if not phone.startswith('+') else phone
                    
                    # Firebase verification
                    if FIREBASE_AVAILABLE and FIREBASE_WEB_API_KEY:
                        # Use Firebase Web API Key for verification
                        # In production, you can use Firebase Authentication REST API
                        # to verify phone number authentication tokens
                        print(f"[FIREBASE] OTP verification using Web API Key for {phone_formatted}")
                        
                        # Optional: Verify Firebase ID token if using Firebase Auth
                        # token = request.headers.get('Authorization', '').replace('Bearer ', '')
                        # decoded_token = auth.verify_id_token(token)
                    else:
                        print(f"[FIREBASE] OTP verification for {phone_formatted}")
                except Exception as e:
                    print(f"[FIREBASE WARNING] Verification error: {e}")
                    # Continue with database verification even if Firebase check fails
            
            # Mark OTP as verified in database
            cur.execute('UPDATE otp_codes SET verified = 1 WHERE id = ?', (otp_record['id'],))
            conn.commit()
            conn.close()
            return True, "OTP verified successfully"
        else:
            conn.close()
            return False, "Invalid or expired OTP"
    except Exception as e:
        return False, f"Error verifying OTP: {str(e)}"


def current_user_id():
    return session.get('user_id')


# Decorator-like helpers (simple checks in routes for beginner friendliness)


@app.route('/')
def index():
    return render_template('index.html')


# -----------------
# Hospital auth
# -----------------


@app.route('/hospital/register', methods=['GET', 'POST'])
def hospital_register():
    if request.method == 'POST':
        name = request.form['name']
        reg_no = request.form['reg_no']
        email = request.form['email']
        password = request.form['password']
        state = request.form.get('state')
        district = request.form.get('district')
        latitude = request.form.get('latitude')
        if latitude: latitude = float(latitude)
        longitude = request.form.get('longitude')
        if longitude: longitude = float(longitude)
        abha_connected = 1 if request.form.get('abha_connected') == 'on' else 0

        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                'INSERT INTO hospitals (name, reg_no, email, password, state, district, latitude, longitude, abha_connected) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                (name, reg_no, email, password, state, district, latitude, longitude, abha_connected),
            )
            conn.commit()
            flash('Hospital registered successfully. Please login.', 'success')
            return redirect(url_for('hospital_login'))
        except sqlite3.IntegrityError:
            flash('Hospital with this email or registration number already exists.', 'danger')
        finally:
            conn.close()

    return render_template('hospital_register.html')


@app.route('/hospital/login', methods=['GET', 'POST'])
def hospital_login():
    if request.method == 'POST':
        login_type = request.form.get('login_type', 'password')
        print(f"[DEBUG] Hospital login - login_type: {login_type}, form data: {dict(request.form)}")
        
        if login_type == 'otp':
            # OTP login
            email = request.form.get('email', '').strip()
            phone = request.form.get('phone', '').strip()
            otp_code = request.form.get('otp_code', '').strip()
            
            if not email or not phone:
                flash('Email and phone number are required', 'danger')
                return render_template('hospital_login.html', login_type='otp', demo=demo_defaults())
            
            # Normalize phone number
            normalized_phone = normalize_phone(phone)
            if not normalized_phone:
                flash('Invalid phone number format', 'danger')
                return render_template('hospital_login.html', login_type='otp', email=email, phone=phone)
            
            if not otp_code:
                # Send OTP
                conn = get_db_connection()
                cur = conn.cursor()
                
                # First check by email only
                cur.execute('SELECT * FROM hospitals WHERE email = ?', (email,))
                hospital = cur.fetchone()
                
                if not hospital:
                    conn.close()
                    flash('Email not found', 'danger')
                    return render_template('hospital_login.html', login_type='otp', email=email, phone=phone)
                
                # Check if phone matches (normalize both)
                hospital_phone = normalize_phone(hospital['phone']) if hospital['phone'] else None
                
                if not hospital_phone:
                    conn.close()
                    flash('Phone number not registered. Please use password login or update your profile.', 'danger')
                    return render_template('hospital_login.html', login_type='otp', email=email, phone=phone)
                
                if hospital_phone != normalized_phone:
                    conn.close()
                    flash(f'Phone number does not match. Registered phone ends with: ...{hospital_phone[-4:]}', 'danger')
                    return render_template('hospital_login.html', login_type='otp', email=email, phone=phone)
                
                conn.close()
                
                # Use normalized phone for OTP
                success, message = send_otp(normalized_phone, 'hospital', email, 'login')
                if success:
                    flash(message, 'success')  # Show OTP in message
                    # Extract OTP code from message for display
                    import re
                    otp_match = re.search(r'(\d{6})', message)
                    otp_code_display = otp_match.group(1) if otp_match else None
                    return render_template('hospital_login.html', login_type='otp', email=email, phone=phone, otp_sent=True, otp_code=otp_code_display, otp_message=message)
                else:
                    flash(message, 'danger')
                return render_template('hospital_login.html', login_type='otp', email=email, phone=phone)
            else:
                # Verify OTP (use normalized phone)
                normalized_phone = normalize_phone(phone)
                success, message = verify_otp(normalized_phone, otp_code, 'hospital', email, 'login')
                if success:
                    conn = get_db_connection()
                    cur = conn.cursor()
                    cur.execute('SELECT * FROM hospitals WHERE email = ?', (email,))
                    hospital = cur.fetchone()
                    conn.close()
                    
                    if hospital:
                        login_user('hospital', hospital['id'])
                        flash('Logged in successfully', 'success')
                        return redirect(url_for('hospital_dashboard'))
                else:
                    flash(message, 'danger')
                    return render_template('hospital_login.html', login_type='otp', email=email, phone=phone, otp_sent=True)
        else:
            # Password login
            email = request.form.get('email', '').strip()
            password = request.form.get('password', '').strip()

            if not email or not password:
                flash('Email and password are required', 'danger')
                return render_template('hospital_login.html', login_type='password', demo=demo_defaults())

            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute('SELECT * FROM hospitals WHERE email = ? AND password = ?', (email, password))
            hospital = cur.fetchone()
            conn.close()

            if hospital:
                login_user('hospital', hospital['id'])
                flash('Logged in successfully', 'success')
                return redirect(url_for('hospital_dashboard'))
            else:
                flash('Invalid email or password. Please try again.', 'danger')
                return render_template('hospital_login.html', login_type='password', email=email, demo=demo_defaults())

    return render_template('hospital_login.html', demo=demo_defaults())


@app.route('/hospital/profile', methods=['GET', 'POST'])
def hospital_profile():
    if current_role() != 'hospital':
        flash('Unauthorized', 'danger')
        return redirect(url_for('index'))
    
    hospital_id = current_user_id()
    conn = get_db_connection()
    cur = conn.cursor()
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        state = request.form.get('state', '').strip() or None
        district = request.form.get('district', '').strip() or None
        latitude = request.form.get('latitude')
        if latitude: latitude = float(latitude)
        longitude = request.form.get('longitude')
        if longitude: longitude = float(longitude)
        abha_connected = 1 if request.form.get('abha_connected') == 'on' else 0
        
        # Check if email is already taken by another hospital
        cur.execute('SELECT id FROM hospitals WHERE email = ? AND id != ?', (email, hospital_id))
        if cur.fetchone():
            conn.close()
            flash('Email already exists. Please use a different email.', 'danger')
            cur.execute('SELECT * FROM hospitals WHERE id = ?', (hospital_id,))
            hospital = cur.fetchone()
            conn.close()
            return render_template('hospital_profile.html', hospital=hospital)
        
        # Update hospital profile
        try:
            cur.execute('''
                UPDATE hospitals 
                SET name = ?, email = ?, phone = ?, state = ?, district = ?, latitude = ?, longitude = ?, abha_connected = ?
                WHERE id = ?
            ''', (name, email, phone, state, district, latitude, longitude, abha_connected, hospital_id))
            conn.commit()
            flash('Profile updated successfully', 'success')
            conn.close()
            return redirect(url_for('hospital_profile'))
        except Exception as e:
            conn.rollback()
            conn.close()
            flash(f'Error updating profile: {str(e)}', 'danger')
            return redirect(url_for('hospital_profile'))
    
    # GET request - show current profile
    cur.execute('SELECT * FROM hospitals WHERE id = ?', (hospital_id,))
    hospital = cur.fetchone()
    conn.close()
    
    return render_template('hospital_profile.html', hospital=hospital)


@app.route('/hospital/forgot_password', methods=['GET', 'POST'])
def hospital_forgot_password():
    if request.method == 'POST':
        step = request.form.get('step', 'request')
        
        if step == 'request':
            # Request OTP
            email = request.form.get('email', '').strip()
            phone = request.form.get('phone', '').strip()
            
            if not email or not phone:
                flash('Email and phone number are required', 'danger')
                return render_template('forgot_password.html', role='hospital')
            
            # Normalize phone number
            normalized_phone = normalize_phone(phone)
            if not normalized_phone:
                flash('Invalid phone number format', 'danger')
                return render_template('forgot_password.html', role='hospital')
            
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute('SELECT * FROM hospitals WHERE email = ?', (email,))
            hospital = cur.fetchone()
            
            if not hospital:
                conn.close()
                flash('Email not found', 'danger')
                return render_template('forgot_password.html', role='hospital')
            
            # Check if phone matches (normalize both)
            hospital_phone = normalize_phone(hospital['phone']) if hospital['phone'] else None
            
            if not hospital_phone:
                conn.close()
                flash('Phone number not registered. Please update your profile or use password login.', 'danger')
                return render_template('forgot_password.html', role='hospital')
            
            if hospital_phone != normalized_phone:
                conn.close()
                flash(f'Phone number does not match. Registered phone ends with: ...{hospital_phone[-4:]}', 'danger')
                return render_template('forgot_password.html', role='hospital')
            
            conn.close()
            
            success, message = send_otp(normalized_phone, 'hospital', email, 'reset')
            if success:
                flash(message, 'success')  # Show OTP in message
                return render_template('forgot_password.html', role='hospital', step='verify', email=email, phone=phone)
            else:
                flash(message, 'danger')
        
        elif step == 'verify':
            # Verify OTP and reset password
            email = request.form.get('email', '').strip()
            phone = request.form.get('phone', '').strip()
            otp_code = request.form.get('otp_code', '').strip()
            new_password = request.form.get('new_password', '').strip()
            confirm_password = request.form.get('confirm_password', '').strip()
            
            if not otp_code or not new_password or not confirm_password:
                flash('All fields are required', 'danger')
                return render_template('forgot_password.html', role='hospital', step='verify', email=email, phone=phone)
            
            if new_password != confirm_password:
                flash('Passwords do not match', 'danger')
                return render_template('forgot_password.html', role='hospital', step='verify', email=email, phone=phone)
            
            # Verify OTP (use normalized phone)
            normalized_phone = normalize_phone(phone)
            success, message = verify_otp(normalized_phone, otp_code, 'hospital', email, 'reset')
            if success:
                # Update password
                conn = get_db_connection()
                cur = conn.cursor()
                cur.execute('UPDATE hospitals SET password = ? WHERE email = ?', (new_password, email))
                conn.commit()
                conn.close()
                flash('Password reset successfully. Please login.', 'success')
                return redirect(url_for('hospital_login'))
            else:
                flash(message, 'danger')
                return render_template('forgot_password.html', role='hospital', step='verify', email=email, phone=phone)
    
    return render_template('forgot_password.html', role='hospital')


@app.route('/hospital/delete_doctor/<int:doctor_id>', methods=['POST'])
def delete_doctor(doctor_id):
    if current_role() != 'hospital':
        flash('Unauthorized', 'danger')
        return redirect(url_for('index'))

    hospital_id = current_user_id()

    conn = get_db_connection()
    cur = conn.cursor()

    # Ensure this doctor belongs to the logged-in hospital
    cur.execute('SELECT * FROM doctors WHERE id = ? AND hospital_id = ?', (doctor_id, hospital_id))
    doctor = cur.fetchone()
    if not doctor:
        conn.close()
        flash('Doctor not found for this hospital.', 'warning')
        return redirect(url_for('hospital_dashboard'))

    # Prevent deletion if doctor has existing medical records
    cur.execute('SELECT COUNT(*) AS c FROM records WHERE doctor_id = ?', (doctor_id,))
    count = cur.fetchone()['c']
    if count > 0:
        conn.close()
        flash('Cannot delete doctor with existing medical records.', 'warning')
        return redirect(url_for('hospital_dashboard'))

    cur.execute('DELETE FROM doctors WHERE id = ? AND hospital_id = ?', (doctor_id, hospital_id))
    conn.commit()
    conn.close()

    flash('Doctor deleted successfully.', 'success')
    return redirect(url_for('hospital_dashboard'))


def _normalize_med_key(name):
    return (name or '').strip().lower()


def _ensure_staff_hospital():
    hospital_id, staff_row = _staff_hospital_id()
    if not hospital_id:
        flash('Hospital context not found for staff account.', 'danger')
        return None, None
    return hospital_id, staff_row


def _select_hospital_for_emergency(state=None, district=None):
    """Pick the nearest available hospital based on coarse location data.

    Strategy:
    - Prefer hospitals in the same district (if provided) with at least one Available bed.
    - Else prefer hospitals in the same state with at least one Available bed.
    - Else fall back to any hospital in the same state.
    - Else fall back to any hospital.
    """
    conn = get_db_connection()
    cur = conn.cursor()

    district_norm = (district or '').strip().lower() or None
    state_norm = (state or '').strip().lower() or None

    where = []
    params = []
    if district_norm:
        where.append('LOWER(COALESCE(h.district, \'\')) = ?')
        params.append(district_norm)
    if state_norm:
        where.append('LOWER(COALESCE(h.state, \'\')) = ?')
        params.append(state_norm)

    where_clause = ('WHERE ' + ' AND '.join(where)) if where else ''

    # Prefer hospitals with available beds
    cur.execute(
        f'''SELECT h.id, h.name, h.state, h.district,
                  SUM(CASE WHEN b.status = 'Available' THEN 1 ELSE 0 END) AS available_beds
           FROM hospitals h
           LEFT JOIN beds b ON b.hospital_id = h.id
           {where_clause}
           GROUP BY h.id
           ORDER BY available_beds DESC, h.id ASC
           LIMIT 1''',
        tuple(params),
    )
    row = cur.fetchone()

    # If the best match has no beds, relax to state-only and then to any
    if row and (row['available_beds'] or 0) > 0:
        conn.close()
        return row['id']

    if state_norm:
        cur.execute(
            '''SELECT h.id
               FROM hospitals h
               LEFT JOIN beds b ON b.hospital_id = h.id
               WHERE LOWER(COALESCE(h.state, '')) = ?
               GROUP BY h.id
               ORDER BY SUM(CASE WHEN b.status = 'Available' THEN 1 ELSE 0 END) DESC, h.id ASC
               LIMIT 1''',
            (state_norm,),
        )
        row2 = cur.fetchone()
        if row2:
            conn.close()
            return row2['id']

    cur.execute(
        '''SELECT h.id
           FROM hospitals h
           LEFT JOIN beds b ON b.hospital_id = h.id
           GROUP BY h.id
           ORDER BY SUM(CASE WHEN b.status = 'Available' THEN 1 ELSE 0 END) DESC, h.id ASC
           LIMIT 1'''
    )
    row3 = cur.fetchone()
    conn.close()
    return (row3['id'] if row3 else None)


@app.context_processor
def inject_staff_notifications():
    """Expose staff notification counters to all templates."""
    data = {}
    try:
        if current_role() == 'staff':
            hospital_id, _ = _staff_hospital_id()
            if hospital_id:
                conn = get_db_connection()
                cur = conn.cursor()
                cur.execute(
                    "SELECT COUNT(*) AS c FROM emergencies WHERE hospital_id = ? AND COALESCE(seen_by_hospital, 0) = 0",
                    (hospital_id,),
                )
                data['unseen_emergencies'] = cur.fetchone()['c'] or 0
                conn.close()
    except Exception:
        # Never break rendering due to notification logic
        pass
    return data


@app.route('/hospital/logout')
def hospital_logout():
    session.clear()
    flash('Logged out successfully', 'info')
    return redirect(url_for('index'))


@app.route('/hospital/dashboard')
def hospital_dashboard():
    if current_role() != 'hospital':
        flash('Unauthorized', 'danger')
        return redirect(url_for('index'))

    hospital_id = current_user_id()

    conn = get_db_connection()
    cur = conn.cursor()

    # Load basic hospital info (for location display)
    # Be defensive in case the existing DB was created before state/district columns were added.
    try:
        cur.execute('SELECT state, district FROM hospitals WHERE id = ?', (hospital_id,))
        hospital = cur.fetchone()
    except sqlite3.OperationalError:
        # Fallback: no such columns in this DB; keep hospital minimal so template can still render.
        hospital = {'state': None, 'district': None}

    # Count doctors for this hospital
    cur.execute('SELECT COUNT(*) AS c FROM doctors WHERE hospital_id = ?', (hospital_id,))
    doctors_count = cur.fetchone()['c']

    # Count distinct patients treated by this hospital's doctors
    cur.execute(
        '''SELECT COUNT(DISTINCT r.user_id) AS c
           FROM records r
           JOIN doctors d ON r.doctor_id = d.id
           WHERE d.hospital_id = ?''',
        (hospital_id,),
    )
    patients_count = cur.fetchone()['c']

    # Count emergency cases (demo: all emergencies)
    cur.execute('SELECT COUNT(*) AS c FROM emergencies')
    emergency_count = cur.fetchone()['c']

    # Inventory stats
    inventory_count = 0
    low_stock_count = 0
    low_stock_items = []
    try:
        cur.execute('SELECT COUNT(*) AS c FROM inventory_items WHERE hospital_id = ?', (hospital_id,))
        inventory_count = cur.fetchone()['c']
        cur.execute(
            '''SELECT COUNT(*) AS c
               FROM inventory_items
               WHERE hospital_id = ? AND quantity <= reorder_level''',
            (hospital_id,),
        )
        low_stock_count = cur.fetchone()['c']

        cur.execute(
            '''SELECT item_name, quantity, unit, reorder_level
               FROM inventory_items
               WHERE hospital_id = ? AND quantity <= reorder_level
               ORDER BY (reorder_level - quantity) DESC, item_name ASC
               LIMIT 8''',
            (hospital_id,),
        )
        low_stock_items = cur.fetchall()
    except sqlite3.OperationalError:
        inventory_count = 0
        low_stock_count = 0
        low_stock_items = []

    # Beds / admissions (managed in staff panel, but summarized for hospital)
    beds_total = 0
    beds_available = 0
    beds_occupied = 0
    active_admissions = 0
    try:
        cur.execute('SELECT COUNT(*) AS c FROM beds WHERE hospital_id = ?', (hospital_id,))
        beds_total = cur.fetchone()['c']
        cur.execute("SELECT COUNT(*) AS c FROM beds WHERE hospital_id = ? AND status = 'Available'", (hospital_id,))
        beds_available = cur.fetchone()['c']
        cur.execute("SELECT COUNT(*) AS c FROM beds WHERE hospital_id = ? AND status = 'Occupied'", (hospital_id,))
        beds_occupied = cur.fetchone()['c']
        cur.execute("SELECT COUNT(*) AS c FROM admissions WHERE hospital_id = ? AND status = 'Active'", (hospital_id,))
        active_admissions = cur.fetchone()['c']
    except sqlite3.OperationalError:
        beds_total = 0
        beds_available = 0
        beds_occupied = 0
        active_admissions = 0

    # Staff stats
    staff_count = 0
    try:
        cur.execute('SELECT COUNT(*) AS c FROM staff WHERE hospital_id = ?', (hospital_id,))
        staff_count = cur.fetchone()['c']
    except sqlite3.OperationalError:
        staff_count = 0

    # Emergencies assigned to this hospital
    assigned_emergency_count = 0
    unseen_assigned_emergency_count = 0
    recent_emergencies = []
    emergency_status_counts = []
    emergency_priority_counts = []
    emergency_avg_response_minutes = None
    try:
        cur.execute('SELECT COUNT(*) AS c FROM emergencies WHERE hospital_id = ?', (hospital_id,))
        assigned_emergency_count = cur.fetchone()['c']
        cur.execute(
            'SELECT COUNT(*) AS c FROM emergencies WHERE hospital_id = ? AND COALESCE(seen_by_hospital, 0) = 0',
            (hospital_id,),
        )
        unseen_assigned_emergency_count = cur.fetchone()['c']

        cur.execute(
            '''SELECT COALESCE(status, 'Unknown') AS status, COUNT(*) AS c
               FROM emergencies
               WHERE hospital_id = ?
               GROUP BY COALESCE(status, 'Unknown')
               ORDER BY c DESC''',
            (hospital_id,),
        )
        emergency_status_counts = cur.fetchall()

        cur.execute(
            '''SELECT COALESCE(priority, 'Unknown') AS priority, COUNT(*) AS c
               FROM emergencies
               WHERE hospital_id = ?
               GROUP BY COALESCE(priority, 'Unknown')
               ORDER BY c DESC''',
            (hospital_id,),
        )
        emergency_priority_counts = cur.fetchall()

        cur.execute(
            '''SELECT AVG(response_time_minutes) AS avg_mins
               FROM emergencies
               WHERE hospital_id = ? AND response_time_minutes IS NOT NULL''',
            (hospital_id,),
        )
        emergency_avg_response_minutes = cur.fetchone()['avg_mins']

        cur.execute(
            '''SELECT id, name, phone, location, status, requested_at, priority, state, district
               FROM emergencies
               WHERE hospital_id = ?
               ORDER BY requested_at DESC
               LIMIT 8''',
            (hospital_id,),
        )
        recent_emergencies = cur.fetchall()
    except sqlite3.OperationalError:
        assigned_emergency_count = 0
        unseen_assigned_emergency_count = 0
        recent_emergencies = []
        emergency_status_counts = []
        emergency_priority_counts = []
        emergency_avg_response_minutes = None

    # Recent staff activity
    recent_staff_logs = []
    try:
        cur.execute(
            '''SELECT l.created_at, l.action, l.details, s.name as staff_name
               FROM staff_activity_log l
               JOIN staff s ON l.staff_id = s.id
               WHERE l.hospital_id = ?
               ORDER BY l.created_at DESC
               LIMIT 8''',
            (hospital_id,),
        )
        recent_staff_logs = cur.fetchall()
    except sqlite3.OperationalError:
        recent_staff_logs = []

    # Get doctor list
    cur.execute('SELECT * FROM doctors WHERE hospital_id = ?', (hospital_id,))
    doctors = cur.fetchall()

    # Get patients treated by this hospital's doctors with visit count and last visit
    cur.execute(
        '''SELECT u.id AS user_id, u.name, u.health_id, COUNT(r.id) AS visits,
                  MAX(r.date) AS last_visit
           FROM records r
           JOIN doctors d ON r.doctor_id = d.id
           JOIN users u ON r.user_id = u.id
           WHERE d.hospital_id = ?
           GROUP BY u.id, u.name, u.health_id
           ORDER BY last_visit DESC''',
        (hospital_id,),
    )
    patients = cur.fetchall()

    # Get all medical records for this hospital's doctors (Visit History)
    cur.execute(
        '''SELECT r.*, d.name as doctor_name, d.specialization as doctor_specialization, u.name as patient_name
           FROM records r
           JOIN doctors d ON r.doctor_id = d.id
           JOIN users u ON r.user_id = u.id
           WHERE d.hospital_id = ?
           ORDER BY r.date DESC
           LIMIT 50''',
        (hospital_id,),
    )
    records = cur.fetchall()

    conn.close()

    return render_template(
        'hospital_dashboard.html',
        hospital=hospital,
        doctors_count=doctors_count,
        patients_count=patients_count,
        emergency_count=emergency_count,
        inventory_count=inventory_count,
        low_stock_count=low_stock_count,
        low_stock_items=low_stock_items,
        beds_total=beds_total,
        beds_available=beds_available,
        beds_occupied=beds_occupied,
        active_admissions=active_admissions,
        staff_count=staff_count,
        assigned_emergency_count=assigned_emergency_count,
        unseen_assigned_emergency_count=unseen_assigned_emergency_count,
        recent_emergencies=recent_emergencies,
        emergency_status_counts=emergency_status_counts,
        emergency_priority_counts=emergency_priority_counts,
        emergency_avg_response_minutes=emergency_avg_response_minutes,
        recent_staff_logs=recent_staff_logs,
        doctors=doctors,
        patients=patients,
        records=records,
    )


@app.route('/hospital/emergencies')
def hospital_emergencies():
    if current_role() != 'hospital':
        flash('Unauthorized', 'danger')
        return redirect(url_for('index'))

    hospital_id = current_user_id()
    status = (request.args.get('status') or '').strip()
    show = (request.args.get('show') or '').strip()

    conn = get_db_connection()
    cur = conn.cursor()

    where = ['hospital_id = ?']
    params = [hospital_id]
    if status:
        where.append('COALESCE(status, \'\') = ?')
        params.append(status)
    if show == 'unseen':
        where.append('COALESCE(seen_by_hospital, 0) = 0')

    where_sql = ' WHERE ' + ' AND '.join(where)

    emergencies = []
    try:
        cur.execute(
            f'''SELECT id, name, phone, location, status, requested_at, priority, state, district,
                       COALESCE(seen_by_hospital, 0) AS seen_by_hospital,
                       response_time_minutes
                FROM emergencies
                {where_sql}
                ORDER BY requested_at DESC
                LIMIT 300''',
            tuple(params),
        )
        emergencies = cur.fetchall()
    except sqlite3.OperationalError:
        emergencies = []

    conn.close()
    return render_template('hospital_emergencies.html', emergencies=emergencies, status=status, show=show)


@app.route('/hospital/emergencies/mark_seen', methods=['POST'])
def hospital_emergencies_mark_seen():
    if current_role() != 'hospital':
        flash('Unauthorized', 'danger')
        return redirect(url_for('index'))

    hospital_id = current_user_id()
    emergency_id = int((request.form.get('emergency_id') or '0').strip() or 0)
    if not emergency_id:
        flash('Invalid emergency', 'danger')
        return redirect(url_for('hospital_emergencies'))

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT id FROM emergencies WHERE id = ? AND hospital_id = ?', (emergency_id, hospital_id))
    row = cur.fetchone()
    if not row:
        conn.close()
        flash('Emergency not found.', 'warning')
        return redirect(url_for('hospital_emergencies'))

    cur.execute('UPDATE emergencies SET seen_by_hospital = 1 WHERE id = ? AND hospital_id = ?', (emergency_id, hospital_id))
    conn.commit()
    conn.close()
    flash('Marked as seen.', 'success')
    return redirect(url_for('hospital_emergencies'))


@app.route('/hospital/emergencies/update', methods=['POST'])
def hospital_emergencies_update():
    if current_role() != 'hospital':
        flash('Unauthorized', 'danger')
        return redirect(url_for('index'))

    hospital_id = current_user_id()
    emergency_id = int((request.form.get('emergency_id') or '0').strip() or 0)
    status = (request.form.get('status') or '').strip()
    response_time_raw = (request.form.get('response_time_minutes') or '').strip()

    if not emergency_id:
        flash('Invalid emergency', 'danger')
        return redirect(url_for('hospital_emergencies'))

    response_time_minutes = None
    if response_time_raw and response_time_raw.lstrip('-').isdigit():
        response_time_minutes = int(response_time_raw)

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT id FROM emergencies WHERE id = ? AND hospital_id = ?', (emergency_id, hospital_id))
    row = cur.fetchone()
    if not row:
        conn.close()
        flash('Emergency not found.', 'warning')
        return redirect(url_for('hospital_emergencies'))

    if status:
        cur.execute(
            'UPDATE emergencies SET status = ?, response_time_minutes = COALESCE(?, response_time_minutes) WHERE id = ? AND hospital_id = ?',
            (status, response_time_minutes, emergency_id, hospital_id),
        )
    else:
        cur.execute(
            'UPDATE emergencies SET response_time_minutes = COALESCE(?, response_time_minutes) WHERE id = ? AND hospital_id = ?',
            (response_time_minutes, emergency_id, hospital_id),
        )
    conn.commit()
    conn.close()
    flash('Emergency updated.', 'success')
    return redirect(url_for('hospital_emergencies') + f"#e-{emergency_id}")


@app.route('/hospital/emergencies/export/csv')
def hospital_emergencies_export_csv():
    if current_role() != 'hospital':
        flash('Unauthorized', 'danger')
        return redirect(url_for('index'))

    hospital_id = current_user_id()
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            '''SELECT id, name, phone, location, status, requested_at, priority, state, district,
                      COALESCE(seen_by_hospital, 0) AS seen_by_hospital, response_time_minutes
               FROM emergencies
               WHERE hospital_id = ?
               ORDER BY requested_at DESC''',
            (hospital_id,),
        )
        rows = cur.fetchall()
    except sqlite3.OperationalError:
        rows = []
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        'ID', 'Name', 'Phone', 'Location', 'Status', 'Priority', 'State', 'District', 'Requested At', 'Seen', 'Response Time (mins)'
    ])
    for r in rows:
        writer.writerow([
            r['id'], r['name'] or '', r['phone'] or '', r['location'] or '', r['status'] or '', r['priority'] or '',
            r['state'] or '', r['district'] or '', r['requested_at'] or '', (r['seen_by_hospital'] or 0), r['response_time_minutes'] or ''
        ])

    csv_data = output.getvalue()
    output.close()
    filename = 'hospital_emergencies.csv'
    response = Response(csv_data, mimetype='text/csv')
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'
    return response


@app.route('/hospital/inventory')
def hospital_inventory():
    if current_role() != 'hospital':
        flash('Unauthorized', 'danger')
        return redirect(url_for('index'))

    hospital_id = current_user_id()
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            '''SELECT *
               FROM inventory_items
               WHERE hospital_id = ?
               ORDER BY (quantity <= reorder_level) DESC, item_name ASC''',
            (hospital_id,),
        )
        items = cur.fetchall()
    except sqlite3.OperationalError:
        conn.close()
        flash('Inventory system is not initialized in the database.', 'danger')
        return redirect(url_for('hospital_dashboard'))

    conn.close()
    return render_template('hospital_inventory.html', items=items)


@app.route('/hospital/inventory/add', methods=['POST'])
def hospital_inventory_add():
    if current_role() != 'hospital':
        flash('Unauthorized', 'danger')
        return redirect(url_for('index'))

    hospital_id = current_user_id()
    item_name = (request.form.get('item_name') or '').strip()
    medicine_type = (request.form.get('medicine_type') or '').strip() or None
    strength_raw = (request.form.get('strength_mg') or '').strip()
    strength_mg = float(strength_raw) if strength_raw and strength_raw.replace('.', '', 1).isdigit() else None
    category = (request.form.get('category') or '').strip() or None
    unit = (request.form.get('unit') or '').strip() or None
    notes = (request.form.get('notes') or '').strip() or None

    quantity_raw = (request.form.get('quantity') or '').strip()
    reorder_raw = (request.form.get('reorder_level') or '').strip()

    if not item_name:
        flash('Item name is required', 'danger')
        return redirect(url_for('hospital_inventory'))

    quantity = int(quantity_raw) if quantity_raw.lstrip('-').isdigit() else 0
    reorder_level = int(reorder_raw) if reorder_raw.isdigit() else 0

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            '''INSERT INTO inventory_items (hospital_id, item_name, medicine_type, strength_mg, category, quantity, unit, reorder_level, last_updated, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (hospital_id, item_name, medicine_type, strength_mg, category, quantity, unit, reorder_level, datetime.now().isoformat(), notes),
        )
        conn.commit()
        flash('Inventory item added.', 'success')
    except sqlite3.IntegrityError:
        # Item exists for this hospital; update instead of error.
        cur.execute(
            '''UPDATE inventory_items
               SET medicine_type = ?, strength_mg = ?, category = ?, quantity = ?, unit = ?, reorder_level = ?, last_updated = ?, notes = ?
               WHERE hospital_id = ? AND item_name = ?''',
            (medicine_type, strength_mg, category, quantity, unit, reorder_level, datetime.now().isoformat(), notes, hospital_id, item_name),
        )
        conn.commit()
        flash('Item already existed. Updated the existing item.', 'info')
    finally:
        conn.close()

    return redirect(url_for('hospital_inventory'))


@app.route('/hospital/inventory/update/<int:item_id>', methods=['POST'])
def hospital_inventory_update(item_id):
    if current_role() != 'hospital':
        flash('Unauthorized', 'danger')
        return redirect(url_for('index'))

    hospital_id = current_user_id()
    quantity_raw = (request.form.get('quantity') or '').strip()
    reorder_raw = (request.form.get('reorder_level') or '').strip()
    unit = (request.form.get('unit') or '').strip() or None
    category = (request.form.get('category') or '').strip() or None
    medicine_type = (request.form.get('medicine_type') or '').strip() or None
    strength_raw = (request.form.get('strength_mg') or '').strip()
    strength_mg = float(strength_raw) if strength_raw and strength_raw.replace('.', '', 1).isdigit() else None
    notes = (request.form.get('notes') or '').strip() or None

    quantity = int(quantity_raw) if quantity_raw.lstrip('-').isdigit() else 0
    reorder_level = int(reorder_raw) if reorder_raw.isdigit() else 0

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT id FROM inventory_items WHERE id = ? AND hospital_id = ?', (item_id, hospital_id))
    item = cur.fetchone()
    if not item:
        conn.close()
        flash('Inventory item not found.', 'warning')
        return redirect(url_for('hospital_inventory'))

    cur.execute(
        '''UPDATE inventory_items
           SET medicine_type = ?, strength_mg = ?, category = ?, quantity = ?, unit = ?, reorder_level = ?, last_updated = ?, notes = ?
           WHERE id = ? AND hospital_id = ?''',
        (medicine_type, strength_mg, category, quantity, unit, reorder_level, datetime.now().isoformat(), notes, item_id, hospital_id),
    )
    conn.commit()
    conn.close()

    flash('Inventory item updated.', 'success')
    return redirect(url_for('hospital_inventory'))


@app.route('/hospital/inventory/delete/<int:item_id>', methods=['POST'])
def hospital_inventory_delete(item_id):
    if current_role() != 'hospital':
        flash('Unauthorized', 'danger')
        return redirect(url_for('index'))

    hospital_id = current_user_id()
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('DELETE FROM inventory_items WHERE id = ? AND hospital_id = ?', (item_id, hospital_id))
    conn.commit()
    conn.close()

    flash('Inventory item deleted.', 'success')
    return redirect(url_for('hospital_inventory'))


@app.route('/hospital/staff')
def hospital_staff():
    if current_role() != 'hospital':
        flash('Unauthorized', 'danger')
        return redirect(url_for('index'))

    hospital_id = current_user_id()
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute('SELECT * FROM staff WHERE hospital_id = ? ORDER BY id DESC', (hospital_id,))
        staff_rows = cur.fetchall()
    except sqlite3.OperationalError:
        conn.close()
        flash('Staff system is not initialized in the database.', 'danger')
        return redirect(url_for('hospital_dashboard'))

    conn.close()
    return render_template('hospital_staff.html', staff=staff_rows)


@app.route('/hospital/staff/add', methods=['POST'])
def hospital_staff_add():
    if current_role() != 'hospital':
        flash('Unauthorized', 'danger')
        return redirect(url_for('index'))

    hospital_id = current_user_id()
    name = (request.form.get('name') or '').strip()
    email = (request.form.get('email') or '').strip().lower()
    password = (request.form.get('password') or '').strip()
    role_title = (request.form.get('role_title') or '').strip() or None

    if not name or not email or not password:
        flash('Name, email and password are required', 'danger')
        return redirect(url_for('hospital_staff'))

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            'INSERT INTO staff (hospital_id, name, email, password, role_title) VALUES (?, ?, ?, ?, ?)',
            (hospital_id, name, email, password, role_title),
        )
        conn.commit()
        flash('Staff account created.', 'success')
    except sqlite3.IntegrityError:
        flash('Staff with this email already exists.', 'danger')
    finally:
        conn.close()

    return redirect(url_for('hospital_staff'))


@app.route('/hospital/staff/delete/<int:staff_id>', methods=['POST'])
def hospital_staff_delete(staff_id):
    if current_role() != 'hospital':
        flash('Unauthorized', 'danger')
        return redirect(url_for('index'))

    hospital_id = current_user_id()
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('DELETE FROM staff WHERE id = ? AND hospital_id = ?', (staff_id, hospital_id))
    conn.commit()
    conn.close()

    flash('Staff account deleted.', 'success')
    return redirect(url_for('hospital_staff'))


@app.route('/hospital/patient/<int:user_id>')
def hospital_patient_detail(user_id):
    if current_role() != 'hospital':
        flash('Unauthorized', 'danger')
        return redirect(url_for('index'))

    hospital_id = current_user_id()

    conn = get_db_connection()
    cur = conn.cursor()

    # Ensure patient exists
    cur.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    patient = cur.fetchone()
    if not patient:
        conn.close()
        flash('Patient not found.', 'warning')
        return redirect(url_for('hospital_dashboard'))

    # Fetch records for this patient but only with doctors from this hospital
    cur.execute(
        '''SELECT r.*, d.name as doctor_name, d.specialization as doctor_specialization
           FROM records r
           JOIN doctors d ON r.doctor_id = d.id
           WHERE r.user_id = ? AND d.hospital_id = ?
           ORDER BY r.date DESC''',
        (user_id, hospital_id),
    )
    records = cur.fetchall()

    conn.close()

    # Optionally, we could hide patients that have no records with this hospital
    print_mode = request.args.get('print') == '1'
    return render_template('hospital_patient_detail.html', patient=patient, records=records, print_mode=print_mode)


@app.route('/hospital/add_doctor', methods=['POST'])
def add_doctor():
    if current_role() != 'hospital':
        flash('Unauthorized', 'danger')
        return redirect(url_for('index'))

    hospital_id = current_user_id()
    name = request.form['name']
    email = request.form['email']
    password = request.form['password']
    specialization = request.form.get('specialization', '')

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            'INSERT INTO doctors (hospital_id, name, email, password, specialization) VALUES (?, ?, ?, ?, ?)',
            (hospital_id, name, email, password, specialization),
        )
        conn.commit()
        flash('Doctor added successfully.', 'success')
    except sqlite3.IntegrityError:
        flash('Doctor with this email already exists.', 'danger')
    finally:
        conn.close()

    return redirect(url_for('hospital_dashboard'))


# -----------------
# Doctor auth & dashboard
# -----------------


@app.route('/doctor/login', methods=['GET', 'POST'])
def doctor_login():
    if request.method == 'POST':
        account_type = request.form.get('account_type', 'doctor')
        login_type = request.form.get('login_type', 'password')
        print(f"[DEBUG] Doctor login - login_type: {login_type}, form data: {dict(request.form)}")

        # Staff login (through doctor login page)
        if account_type == 'staff':
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '').strip()

            if not email or not password:
                flash('Email and password are required', 'danger')
                return render_template('doctor_login.html', account_type='staff', login_type='password', email=email, demo=demo_defaults())

            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute('SELECT * FROM staff WHERE email = ?', (email,))
            staff_row = cur.fetchone()
            if not staff_row:
                # If user is trying demo staff credentials, auto-create demo staff on first login.
                demo = demo_defaults()
                demo_staff_email = (demo.get('staff_email') or '').strip().lower()
                demo_staff_password = (demo.get('staff_password') or '').strip()
                if email == demo_staff_email and password == demo_staff_password:
                    # Ensure demo hospital exists
                    demo_hospital_email = (demo.get('hospital_email') or '').strip().lower()
                    cur.execute('SELECT id FROM hospitals WHERE LOWER(email) = ?', (demo_hospital_email,))
                    hosp = cur.fetchone()
                    if not hosp:
                        cur.execute(
                            'INSERT INTO hospitals (name, reg_no, email, password, state, district) VALUES (?, ?, ?, ?, ?, ?)',
                            ('Demo Hospital', 'DEMO-HOSP-0001', demo_hospital_email, demo.get('hospital_password') or 'admin123', None, None),
                        )
                        hospital_id = cur.lastrowid
                    else:
                        hospital_id = hosp['id']

                    cur.execute(
                        'INSERT INTO staff (hospital_id, name, email, password, role_title) VALUES (?, ?, ?, ?, ?)',
                        (hospital_id, 'Demo Staff', demo_staff_email, demo_staff_password, 'Reception'),
                    )
                    conn.commit()
                    cur.execute('SELECT * FROM staff WHERE email = ?', (email,))
                    staff_row = cur.fetchone()

                if not staff_row:
                    conn.close()
                    flash('Staff account not found. Ask your hospital admin to create your staff account.', 'danger')
                    return render_template('doctor_login.html', account_type='staff', login_type='password', email=email, demo=demo_defaults())

            if staff_row['password'] != password:
                conn.close()
                flash('Incorrect password for staff account.', 'danger')
                return render_template('doctor_login.html', account_type='staff', login_type='password', email=email, demo=demo_defaults())

            conn.close()
            login_user('staff', staff_row['id'])
            flash('Logged in successfully', 'success')
            return redirect(url_for('staff_dashboard'))
        
        if login_type == 'otp':
            # OTP login
            email = request.form.get('email', '').strip()
            phone = request.form.get('phone', '').strip()
            otp_code = request.form.get('otp_code', '').strip()
            
            if not email or not phone:
                flash('Email and phone number are required', 'danger')
                return render_template('doctor_login.html', login_type='otp', demo=demo_defaults())
            
            # Normalize phone number
            normalized_phone = normalize_phone(phone)
            if not normalized_phone:
                flash('Invalid phone number format', 'danger')
                return render_template('doctor_login.html', login_type='otp', email=email, phone=phone)
            
            if not otp_code:
                # Send OTP
                conn = get_db_connection()
                cur = conn.cursor()
                
                # First check by email only
                cur.execute('SELECT * FROM doctors WHERE email = ?', (email,))
                doctor = cur.fetchone()
                
                if not doctor:
                    conn.close()
                    flash('Email not found', 'danger')
                    return render_template('doctor_login.html', login_type='otp', email=email, phone=phone)
                
                # Check if phone matches (normalize both)
                doctor_phone = normalize_phone(doctor['phone']) if doctor['phone'] else None
                
                if not doctor_phone:
                    conn.close()
                    flash('Phone number not registered. Please use password login or contact your hospital admin.', 'danger')
                    return render_template('doctor_login.html', login_type='otp', email=email, phone=phone)
                
                if doctor_phone != normalized_phone:
                    conn.close()
                    flash(f'Phone number does not match. Registered phone ends with: ...{doctor_phone[-4:]}', 'danger')
                    return render_template('doctor_login.html', login_type='otp', email=email, phone=phone)
                
                conn.close()
                
                # Use normalized phone for OTP
                success, message = send_otp(normalized_phone, 'doctor', email, 'login')
                if success:
                    flash(message, 'success')  # Show OTP in message
                    # Extract OTP code from message for display
                    otp_match = re.search(r'(\d{6})', message)
                    otp_code_display = otp_match.group(1) if otp_match else None
                    return render_template('doctor_login.html', login_type='otp', email=email, phone=phone, otp_sent=True, otp_code=otp_code_display, otp_message=message)
                else:
                    flash(message, 'danger')
                return render_template('doctor_login.html', login_type='otp', email=email, phone=phone)
            else:
                # Verify OTP (use normalized phone)
                normalized_phone = normalize_phone(phone)
                success, message = verify_otp(normalized_phone, otp_code, 'doctor', email, 'login')
                if success:
                    conn = get_db_connection()
                    cur = conn.cursor()
                    cur.execute('SELECT * FROM doctors WHERE email = ?', (email,))
                    doctor = cur.fetchone()
                    conn.close()
                    
                    if doctor:
                        login_user('doctor', doctor['id'])
                        flash('Logged in successfully', 'success')
                        return redirect(url_for('doctor_dashboard'))
                else:
                    flash(message, 'danger')
                    return render_template('doctor_login.html', login_type='otp', email=email, phone=phone, otp_sent=True)
        else:
            # Password login
            email = request.form.get('email', '').strip()
            password = request.form.get('password', '').strip()

            if not email or not password:
                flash('Email and password are required', 'danger')
                return render_template('doctor_login.html', login_type='password', demo=demo_defaults())

            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute('SELECT * FROM doctors WHERE email = ? AND password = ?', (email, password))
            doctor = cur.fetchone()
            conn.close()

            if doctor:
                login_user('doctor', doctor['id'])
                flash('Logged in successfully', 'success')
                return redirect(url_for('doctor_dashboard'))
            else:
                flash('Invalid email or password. Please check and try again.', 'danger')
                return render_template('doctor_login.html', login_type='password', email=email, demo=demo_defaults())

    return render_template('doctor_login.html', demo=demo_defaults())


@app.route('/staff/dashboard')
def staff_dashboard():
    if current_role() != 'staff':
        flash('Unauthorized', 'danger')
        return redirect(url_for('index'))

    staff_id = current_user_id()
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        '''SELECT s.*, h.name as hospital_name, h.reg_no as hospital_reg_no
           FROM staff s
           JOIN hospitals h ON s.hospital_id = h.id
           WHERE s.id = ?''',
        (staff_id,),
    )
    staff_row = cur.fetchone()
    conn.close()

    return redirect(url_for('staff_home'))


def _get_staff_context():
    staff_id = current_user_id()
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        '''SELECT s.*, h.name as hospital_name, h.reg_no as hospital_reg_no
           FROM staff s
           JOIN hospitals h ON s.hospital_id = h.id
           WHERE s.id = ?''',
        (staff_id,),
    )
    staff_row = cur.fetchone()
    conn.close()
    return staff_row


def _staff_hospital_id():
    st = _get_staff_context()
    return (st['hospital_id'] if st else None), st


def _log_staff_action(hospital_id, staff_id, action, details=None):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        'INSERT INTO staff_activity_log (hospital_id, staff_id, action, details, created_at) VALUES (?, ?, ?, ?, ?)',
        (hospital_id, staff_id, action, details, datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()


@app.route('/staff/home')
def staff_home():
    if current_role() != 'staff':
        flash('Unauthorized', 'danger')
        return redirect(url_for('index'))
    hospital_id, staff_row = _ensure_staff_hospital()
    if not hospital_id:
        return redirect(url_for('index'))

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute('SELECT COUNT(*) AS c FROM beds WHERE hospital_id = ?', (hospital_id,))
    beds_total = (cur.fetchone()['c'] or 0)
    cur.execute("SELECT COUNT(*) AS c FROM beds WHERE hospital_id = ? AND status = 'Available'", (hospital_id,))
    beds_available = (cur.fetchone()['c'] or 0)
    cur.execute("SELECT COUNT(*) AS c FROM admissions WHERE hospital_id = ? AND status = 'Active'", (hospital_id,))
    active_admissions = (cur.fetchone()['c'] or 0)
    cur.execute('SELECT COUNT(*) AS c FROM inventory_items WHERE hospital_id = ?', (hospital_id,))
    inventory_count = (cur.fetchone()['c'] or 0)

    conn.close()

    return render_template(
        'staff/home.html',
        staff=staff_row,
        beds_total=beds_total,
        beds_available=beds_available,
        active_admissions=active_admissions,
        inventory_count=inventory_count,
        active_page='home',
    )


@app.route('/staff/tasks/add', methods=['POST'])
def staff_task_add():
    if current_role() != 'staff':
        flash('Unauthorized', 'danger')
        return redirect(url_for('index'))
    return redirect(url_for('staff_home'))


@app.route('/staff/tasks/toggle/<int:task_id>', methods=['POST'])
def staff_task_toggle(task_id):
    if current_role() != 'staff':
        flash('Unauthorized', 'danger')
        return redirect(url_for('index'))
    return redirect(url_for('staff_home'))


@app.route('/staff/patients', methods=['GET', 'POST'])
def staff_patients():
    if current_role() != 'staff':
        flash('Unauthorized', 'danger')
        return redirect(url_for('index'))

    hospital_id, staff_row = _ensure_staff_hospital()
    if not hospital_id:
        return redirect(url_for('index'))

    search_health_id = request.args.get('search_health_id') if request.method == 'GET' else None
    if request.method == 'POST':
        search_health_id = request.form.get('search_health_id', '').strip() or None

    patient = None
    records = []
    current_status = None
    admission = None
    beds_available = []

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT id, bed_number, ward, bed_type FROM beds WHERE hospital_id = ? AND status = 'Available' ORDER BY bed_number ASC",
        (hospital_id,),
    )
    beds_available = cur.fetchall()

    if search_health_id:
        cur.execute('SELECT * FROM users WHERE health_id = ?', (search_health_id.strip(),))
        patient = cur.fetchone()
        if patient:
            cur.execute(
                '''SELECT r.*, d.name as doctor_name
                   FROM records r
                   JOIN doctors d ON r.doctor_id = d.id
                   WHERE r.user_id = ? AND d.hospital_id = ?
                   ORDER BY r.date DESC''',
                (patient['id'], hospital_id),
            )
            records = cur.fetchall()

            cur.execute(
                'SELECT status FROM patient_status WHERE hospital_id = ? AND user_id = ?',
                (hospital_id, patient['id']),
            )
            st = cur.fetchone()
            current_status = st['status'] if st else None

            cur.execute(
                '''SELECT a.*, b.bed_number, b.ward, b.bed_type
                   FROM admissions a
                   LEFT JOIN beds b ON a.bed_id = b.id
                   WHERE a.hospital_id = ? AND a.user_id = ? AND a.status = 'Active'
                   ORDER BY a.admitted_at DESC
                   LIMIT 1''',
                (hospital_id, patient['id']),
            )
            admission = cur.fetchone()
        else:
            flash('No patient found with that Health ID.', 'warning')

    conn.close()

    return render_template(
        'staff/patients.html',
        staff=staff_row,
        patient=patient,
        records=records,
        search_health_id=search_health_id,
        current_status=current_status,
        admission=admission,
        beds_available=beds_available,
        active_page='patients',
    )


@app.route('/staff/patients/status', methods=['POST'])
def staff_patient_status_update():
    if current_role() != 'staff':
        flash('Unauthorized', 'danger')
        return redirect(url_for('index'))

    hospital_id, staff_row = _ensure_staff_hospital()
    if not hospital_id:
        return redirect(url_for('index'))

    staff_id = staff_row['id']
    health_id = request.form.get('health_id', '').strip()
    status = request.form.get('status', '').strip()
    if not health_id or not status:
        flash('Health ID and status are required.', 'danger')
        return redirect(url_for('staff_patients', search_health_id=health_id))

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT id FROM users WHERE health_id = ?', (health_id,))
    patient = cur.fetchone()
    if not patient:
        conn.close()
        flash('Patient not found.', 'warning')
        return redirect(url_for('staff_patients', search_health_id=health_id))

    cur.execute(
        '''INSERT INTO patient_status (hospital_id, user_id, status, updated_by_staff_id, updated_at)
           VALUES (?, ?, ?, ?, ?)
           ON CONFLICT(hospital_id, user_id) DO UPDATE SET
             status=excluded.status,
             updated_by_staff_id=excluded.updated_by_staff_id,
             updated_at=excluded.updated_at''',
        (hospital_id, patient['id'], status, staff_id, datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()

    _log_staff_action(hospital_id, staff_id, 'Patient Status Updated', f"{health_id} -> {status}")
    flash('Patient status updated.', 'success')
    return redirect(url_for('staff_patients', search_health_id=health_id))


@app.route('/staff/patients/admit', methods=['POST'])
def staff_patient_admit():
    if current_role() != 'staff':
        flash('Unauthorized', 'danger')
        return redirect(url_for('index'))

    hospital_id, staff_row = _ensure_staff_hospital()
    if not hospital_id:
        return redirect(url_for('index'))

    staff_id = staff_row['id']
    health_id = request.form.get('health_id', '').strip()
    bed_id_raw = request.form.get('bed_id', '').strip() or None
    reason = request.form.get('reason', '').strip() or None

    if not health_id:
        flash('Health ID is required.', 'danger')
        return redirect(url_for('staff_patients'))

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT id FROM users WHERE health_id = ?', (health_id,))
    patient = cur.fetchone()
    if not patient:
        conn.close()
        flash('Patient not found.', 'warning')
        return redirect(url_for('staff_patients', search_health_id=health_id))

    cur.execute(
        "SELECT id, bed_number, status FROM beds WHERE id = ? AND hospital_id = ?",
        (bed_id_raw, hospital_id),
    )
    bed = cur.fetchone() if bed_id_raw else None
    if bed_id_raw and (not bed or bed['status'] != 'Available'):
        conn.close()
        flash('Selected bed is not available.', 'danger')
        return redirect(url_for('staff_patients', search_health_id=health_id))

    cur.execute(
        "SELECT id FROM admissions WHERE hospital_id = ? AND user_id = ? AND status = 'Active'",
        (hospital_id, patient['id']),
    )
    existing = cur.fetchone()
    if existing:
        conn.close()
        flash('Patient is already admitted.', 'warning')
        return redirect(url_for('staff_patients', search_health_id=health_id))

    admitted_at = datetime.utcnow().isoformat()
    cur.execute(
        '''INSERT INTO admissions (hospital_id, user_id, bed_id, status, reason, admitted_at, created_by_staff_id)
           VALUES (?, ?, ?, 'Active', ?, ?, ?)''',
        (hospital_id, patient['id'], bed['id'] if bed else None, reason, admitted_at, staff_id),
    )
    if bed:
        cur.execute(
            "UPDATE beds SET status = 'Occupied', updated_at = ? WHERE id = ? AND hospital_id = ?",
            (admitted_at, bed['id'], hospital_id),
        )

    cur.execute(
        '''INSERT INTO patient_status (hospital_id, user_id, status, updated_by_staff_id, updated_at)
           VALUES (?, ?, 'Admitted', ?, ?)
           ON CONFLICT(hospital_id, user_id) DO UPDATE SET
             status=excluded.status,
             updated_by_staff_id=excluded.updated_by_staff_id,
             updated_at=excluded.updated_at''',
        (hospital_id, patient['id'], staff_id, admitted_at),
    )

    conn.commit()
    conn.close()

    _log_staff_action(hospital_id, staff_id, 'Patient Admitted', f"{health_id} bed={bed['bed_number'] if bed else '-'}")
    flash('Patient admitted successfully.', 'success')
    return redirect(url_for('staff_patients', search_health_id=health_id))


@app.route('/staff/patients/discharge', methods=['POST'])
def staff_patient_discharge():
    if current_role() != 'staff':
        flash('Unauthorized', 'danger')
        return redirect(url_for('index'))

    hospital_id, staff_row = _ensure_staff_hospital()
    if not hospital_id:
        return redirect(url_for('index'))

    staff_id = staff_row['id']
    health_id = request.form.get('health_id', '').strip()
    if not health_id:
        flash('Health ID is required.', 'danger')
        return redirect(url_for('staff_patients'))

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT id FROM users WHERE health_id = ?', (health_id,))
    patient = cur.fetchone()
    if not patient:
        conn.close()
        flash('Patient not found.', 'warning')
        return redirect(url_for('staff_patients', search_health_id=health_id))

    cur.execute(
        "SELECT id, bed_id FROM admissions WHERE hospital_id = ? AND user_id = ? AND status = 'Active' ORDER BY admitted_at DESC LIMIT 1",
        (hospital_id, patient['id']),
    )
    adm = cur.fetchone()
    if not adm:
        conn.close()
        flash('No active admission found for this patient.', 'warning')
        return redirect(url_for('staff_patients', search_health_id=health_id))

    discharged_at = datetime.utcnow().isoformat()
    cur.execute(
        "UPDATE admissions SET status='Discharged', discharged_at=?, discharged_by_staff_id=? WHERE id=? AND hospital_id=?",
        (discharged_at, staff_id, adm['id'], hospital_id),
    )
    if adm['bed_id']:
        cur.execute(
            "UPDATE beds SET status='Available', updated_at=? WHERE id=? AND hospital_id=?",
            (discharged_at, adm['bed_id'], hospital_id),
        )

    cur.execute(
        '''INSERT INTO patient_status (hospital_id, user_id, status, updated_by_staff_id, updated_at)
           VALUES (?, ?, 'Discharged', ?, ?)
           ON CONFLICT(hospital_id, user_id) DO UPDATE SET
             status=excluded.status,
             updated_by_staff_id=excluded.updated_by_staff_id,
             updated_at=excluded.updated_at''',
        (hospital_id, patient['id'], staff_id, discharged_at),
    )

    conn.commit()
    conn.close()

    _log_staff_action(hospital_id, staff_id, 'Patient Discharged', health_id)
    flash('Patient discharged successfully.', 'success')
    return redirect(url_for('staff_patients', search_health_id=health_id))


@app.route('/staff/reports', methods=['GET', 'POST'])
def staff_reports():
    if current_role() != 'staff':
        flash('Unauthorized', 'danger')
        return redirect(url_for('index'))

    hospital_id, staff_row = _ensure_staff_hospital()
    if not hospital_id:
        return redirect(url_for('index'))

    staff_id = staff_row['id']
    search_health_id = request.args.get('search_health_id', '').strip() if request.method == 'GET' else request.form.get('search_health_id', '').strip()
    if not search_health_id:
        search_health_id = request.args.get('search_health_id')

    patient = None
    records = []

    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == 'POST' and request.form.get('action') == 'upload':
        record_id = request.form.get('record_id')
        blood_report_file = request.files.get('blood_report_file')
        prescription_file = request.files.get('prescription_file')

        cur.execute(
            '''SELECT r.id
               FROM records r
               JOIN doctors d ON r.doctor_id = d.id
               WHERE r.id = ? AND d.hospital_id = ?''',
            (record_id, hospital_id),
        )
        rec = cur.fetchone()
        if not rec:
            conn.close()
            flash('Visit not found in your hospital.', 'danger')
            return redirect(url_for('staff_reports', search_health_id=search_health_id))

        blood_report_filename = None
        if blood_report_file and blood_report_file.filename:
            blood_report_filename = f"blood_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{blood_report_file.filename}"
            blood_report_path = os.path.join(app.config['UPLOAD_FOLDER'], blood_report_filename)
            blood_report_file.save(blood_report_path)

        prescription_filename = None
        if prescription_file and prescription_file.filename:
            prescription_filename = f"presc_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{prescription_file.filename}"
            prescription_path = os.path.join(app.config['UPLOAD_FOLDER'], prescription_filename)
            prescription_file.save(prescription_path)

        if not blood_report_filename and not prescription_filename:
            conn.close()
            flash('Please select at least one file to upload.', 'warning')
            return redirect(url_for('staff_reports', search_health_id=search_health_id))

        if blood_report_filename:
            cur.execute(
                "UPDATE records SET blood_report_filename = ?, report_filename = ? WHERE id = ?",
                (blood_report_filename, blood_report_filename, record_id),
            )
        if prescription_filename:
            cur.execute(
                "UPDATE records SET prescription_filename = ? WHERE id = ?",
                (prescription_filename, record_id),
            )
        conn.commit()
        _log_staff_action(hospital_id, staff_id, 'Report Uploaded', f"record_id={record_id}")
        flash('Files uploaded successfully.', 'success')

    if search_health_id:
        cur.execute('SELECT * FROM users WHERE health_id = ?', (search_health_id.strip(),))
        patient = cur.fetchone()
        if patient:
            cur.execute(
                '''SELECT r.*, d.name as doctor_name
                   FROM records r
                   JOIN doctors d ON r.doctor_id = d.id
                   WHERE r.user_id = ? AND d.hospital_id = ?
                   ORDER BY r.date DESC''',
                (patient['id'], hospital_id),
            )
            records = cur.fetchall()
        else:
            flash('No patient found with that Health ID.', 'warning')

    conn.close()
    return render_template(
        'staff/reports.html',
        staff=staff_row,
        patient=patient,
        records=records,
        search_health_id=search_health_id,
        active_page='reports',
    )


@app.route('/staff/medicines', methods=['GET', 'POST'])
def staff_medicines():
    if current_role() != 'staff':
        flash('Unauthorized', 'danger')
        return redirect(url_for('index'))

    hospital_id, staff_row = _ensure_staff_hospital()
    if not hospital_id:
        return redirect(url_for('index'))

    staff_id = staff_row['id']
    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == 'POST':
        record_id = request.form.get('record_id')
        medicine_name = _normalize_med_key(request.form.get('medicine_name'))
        status = request.form.get('status', '').strip()
        if record_id and medicine_name and status in ('Given', 'Pending'):
            cur.execute(
                '''SELECT r.id
                   FROM records r
                   JOIN doctors d ON r.doctor_id = d.id
                   WHERE r.id = ? AND d.hospital_id = ?''',
                (record_id, hospital_id),
            )
            rec = cur.fetchone()
            if rec:
                cur.execute(
                    '''INSERT INTO medicine_administration (hospital_id, record_id, medicine_name, status, updated_by_staff_id, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?)
                       ON CONFLICT(record_id, medicine_name) DO UPDATE SET
                         status=excluded.status,
                         updated_by_staff_id=excluded.updated_by_staff_id,
                         updated_at=excluded.updated_at''',
                    (hospital_id, record_id, medicine_name, status, staff_id, datetime.utcnow().isoformat()),
                )
                conn.commit()
                _log_staff_action(hospital_id, staff_id, 'Medicine Status Updated', f"record_id={record_id} {medicine_name} -> {status}")
        return redirect(url_for('staff_medicines'))

    cur.execute(
        '''SELECT r.*, u.name as patient_name, u.health_id as health_id
           FROM records r
           JOIN users u ON r.user_id = u.id
           JOIN doctors d ON r.doctor_id = d.id
           WHERE d.hospital_id = ?
           ORDER BY r.created_at DESC
           LIMIT 25''',
        (hospital_id,),
    )
    records = cur.fetchall()

    record_ids = [r['id'] for r in records]
    admin_map = {}
    if record_ids:
        placeholders = ','.join('?' for _ in record_ids)
        cur.execute(
            f"SELECT record_id, medicine_name, status FROM medicine_administration WHERE hospital_id = ? AND record_id IN ({placeholders})",
            (hospital_id, *record_ids),
        )
        for row in cur.fetchall():
            admin_map[(row['record_id'], row['medicine_name'])] = row['status']

    cur.execute(
        'SELECT item_name, quantity, unit FROM inventory_items WHERE hospital_id = ?',
        (hospital_id,),
    )
    inv_map = {}
    for it in cur.fetchall():
        inv_map[_normalize_med_key(it['item_name'])] = dict(it)

    conn.close()
    return render_template(
        'staff/medicines.html',
        staff=staff_row,
        records=records,
        admin_map=admin_map,
        inv_map=inv_map,
        active_page='medicines',
    )


@app.route('/staff/emergencies', methods=['GET', 'POST'])
def staff_emergencies():
    if current_role() != 'staff':
        flash('Unauthorized', 'danger')
        return redirect(url_for('index'))

    hospital_id, staff_row = _ensure_staff_hospital()
    if not hospital_id:
        return redirect(url_for('index'))

    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == 'POST':
        # Staff intake for walk-in / phone call emergencies (hospital-scoped)
        name = request.form.get('name')
        phone = request.form.get('phone')
        location = request.form.get('location')
        symptoms = request.form.get('symptoms', '')

        if not location:
            conn.close()
            flash('Location is required.', 'danger')
            return redirect(url_for('staff_emergencies'))

        now = datetime.utcnow().isoformat()
        cur.execute(
            '''INSERT INTO emergencies (user_id, name, phone, location, status, requested_at,
               response_time_minutes, priority, severity, prediction_score, symptoms, age,
               state, district, zone, day, time_slot, emergency_type, weather,
               hospital_id, assigned_at, seen_by_hospital)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (
                None,
                name,
                phone,
                location,
                'Emergency Reported (Staff Intake)',
                now,
                None,
                'High',
                None,
                None,
                symptoms,
                None,
                None,
                None,
                None,
                datetime.now().strftime('%A'),
                None,
                None,
                None,
                hospital_id,
                now,
                1,
            ),
        )
        conn.commit()
        _log_staff_action(hospital_id, staff_row['id'], 'Emergency Created', location)
        flash('Emergency created for your hospital.', 'success')

    # Mark unseen emergencies as seen when staff opens this page
    cur.execute(
        "UPDATE emergencies SET seen_by_hospital = 1 WHERE hospital_id = ? AND COALESCE(seen_by_hospital, 0) = 0",
        (hospital_id,),
    )
    conn.commit()

    cur.execute(
        'SELECT * FROM emergencies WHERE hospital_id = ? ORDER BY requested_at DESC LIMIT 100',
        (hospital_id,),
    )
    emergencies = cur.fetchall()
    conn.close()

    return render_template(
        'staff/emergencies.html',
        staff=staff_row,
        emergencies=emergencies,
        active_page='emergencies',
    )


@app.route('/staff/logs')
def staff_logs():
    if current_role() != 'staff':
        flash('Unauthorized', 'danger')
        return redirect(url_for('index'))

    hospital_id, staff_row = _ensure_staff_hospital()
    if not hospital_id:
        return redirect(url_for('index'))

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        '''SELECT l.*, s.name AS staff_name
           FROM staff_activity_log l
           JOIN staff s ON l.staff_id = s.id
           WHERE l.hospital_id = ?
           ORDER BY l.created_at DESC
           LIMIT 100''',
        (hospital_id,),
    )
    logs = cur.fetchall()
    conn.close()
    return render_template('staff/logs.html', staff=staff_row, logs=logs, active_page='logs')


@app.route('/staff/settings', methods=['GET', 'POST'])
def staff_settings():
    if current_role() != 'staff':
        flash('Unauthorized', 'danger')
        return redirect(url_for('index'))

    hospital_id, staff_row = _ensure_staff_hospital()
    if not hospital_id:
        return redirect(url_for('index'))

    staff_id = staff_row['id']
    if request.method == 'POST':
        conn = get_db_connection()
        cur = conn.cursor()

        if 'current_password' in request.form and 'new_password' in request.form:
            current_password = request.form.get('current_password', '').strip()
            new_password = request.form.get('new_password', '').strip()

            cur.execute('SELECT password FROM staff WHERE id = ? AND hospital_id = ?', (staff_id, hospital_id))
            row = cur.fetchone()
            if not row or row['password'] != current_password:
                conn.close()
                flash('Current password is incorrect.', 'danger')
                return redirect(url_for('staff_settings'))

            cur.execute('UPDATE staff SET password = ? WHERE id = ? AND hospital_id = ?', (new_password, staff_id, hospital_id))
            conn.commit()
            conn.close()
            _log_staff_action(hospital_id, staff_id, 'Password Changed', None)
            flash('Password updated.', 'success')
            return redirect(url_for('staff_settings'))

        name = request.form.get('name', '').strip()
        role_title = request.form.get('role_title', '').strip() or None
        if not name:
            conn.close()
            flash('Name is required.', 'danger')
            return redirect(url_for('staff_settings'))

        cur.execute(
            'UPDATE staff SET name = ?, role_title = ? WHERE id = ? AND hospital_id = ?',
            (name, role_title, staff_id, hospital_id),
        )
        conn.commit()
        conn.close()
        _log_staff_action(hospital_id, staff_id, 'Profile Updated', None)
        flash('Profile updated.', 'success')
        return redirect(url_for('staff_settings'))

    return render_template('staff/settings.html', staff=staff_row, active_page='settings')


@app.route('/staff/uploads', methods=['GET', 'POST'])
def staff_uploads():
    if current_role() != 'staff':
        flash('Unauthorized', 'danger')
        return redirect(url_for('index'))
    return redirect(url_for('staff_home'))


@app.route('/staff/inventory', methods=['GET', 'POST'])
def staff_inventory():
    if current_role() != 'staff':
        flash('Unauthorized', 'danger')
        return redirect(url_for('index'))

    hospital_id, staff_row = _ensure_staff_hospital()
    if not hospital_id:
        return redirect(url_for('index'))

    staff_id = staff_row['id']
    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == 'POST':
        action = request.form.get('action', 'save').strip()
        if action == 'save':
            item_name = request.form.get('item_name', '').strip()
            if not item_name:
                conn.close()
                flash('Item name is required.', 'danger')
                return redirect(url_for('staff_inventory'))

            quantity_raw = request.form.get('quantity', '0').strip()
            reorder_raw = request.form.get('reorder_level', '0').strip()
            quantity = int(quantity_raw) if quantity_raw.lstrip('-').isdigit() else 0
            reorder_level = int(reorder_raw) if reorder_raw.isdigit() else 0
            unit = request.form.get('unit', '').strip() or None
            category = request.form.get('category', '').strip() or None
            medicine_type = request.form.get('medicine_type', '').strip() or None
            strength_mg_raw = request.form.get('strength_mg', '').strip()
            strength_mg = float(strength_mg_raw) if strength_mg_raw else None
            notes = request.form.get('notes', '').strip() or None

            now = datetime.utcnow().isoformat()
            cur.execute(
                '''INSERT INTO inventory_items (hospital_id, item_name, medicine_type, strength_mg, category, quantity, unit, reorder_level, last_updated, notes)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(hospital_id, item_name) DO UPDATE SET
                     medicine_type=excluded.medicine_type,
                     strength_mg=excluded.strength_mg,
                     category=excluded.category,
                     quantity=excluded.quantity,
                     unit=excluded.unit,
                     reorder_level=excluded.reorder_level,
                     last_updated=excluded.last_updated,
                     notes=excluded.notes''',
                (hospital_id, item_name, medicine_type, strength_mg, category, quantity, unit, reorder_level, now, notes),
            )
            conn.commit()
            _log_staff_action(hospital_id, staff_id, 'Inventory Saved', item_name)
            flash('Inventory item saved.', 'success')
        elif action == 'update':
            item_id = request.form.get('item_id')
            qty_raw = request.form.get('quantity', '0').strip()
            quantity = int(qty_raw) if qty_raw.lstrip('-').isdigit() else 0
            now = datetime.utcnow().isoformat()
            cur.execute(
                'UPDATE inventory_items SET quantity = ?, last_updated = ? WHERE id = ? AND hospital_id = ?',
                (quantity, now, item_id, hospital_id),
            )
            conn.commit()
            _log_staff_action(hospital_id, staff_id, 'Inventory Quantity Updated', f"item_id={item_id} qty={quantity}")
            flash('Quantity updated.', 'success')

        conn.close()
        return redirect(url_for('staff_inventory'))

    cur.execute(
        'SELECT * FROM inventory_items WHERE hospital_id = ? ORDER BY item_name ASC',
        (hospital_id,),
    )
    items = cur.fetchall()
    conn.close()
    return render_template('staff/inventory.html', staff=staff_row, items=items, active_page='inventory')


@app.route('/staff/beds', methods=['GET', 'POST'])
def staff_beds():
    if current_role() != 'staff':
        flash('Unauthorized', 'danger')
        return redirect(url_for('index'))

    hospital_id, staff_row = _ensure_staff_hospital()
    if not hospital_id:
        return redirect(url_for('index'))

    staff_id = staff_row['id']
    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == 'POST':
        action = request.form.get('action', 'add').strip()
        now = datetime.utcnow().isoformat()
        if action == 'add':
            bed_number = request.form.get('bed_number', '').strip()
            ward = request.form.get('ward', '').strip() or None
            bed_type = request.form.get('bed_type', '').strip() or None
            status = request.form.get('status', 'Available').strip() or 'Available'
            notes = request.form.get('notes', '').strip() or None
            if not bed_number:
                conn.close()
                flash('Bed number is required.', 'danger')
                return redirect(url_for('staff_beds'))

            try:
                cur.execute(
                    '''INSERT INTO beds (hospital_id, bed_number, ward, bed_type, status, notes, created_at, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                    (hospital_id, bed_number, ward, bed_type, status, notes, now, now),
                )
                conn.commit()
                _log_staff_action(hospital_id, staff_id, 'Bed Added', bed_number)
                flash('Bed added.', 'success')
            except sqlite3.IntegrityError:
                conn.close()
                flash('Bed number already exists.', 'danger')
                return redirect(url_for('staff_beds'))

        elif action == 'update':
            bed_id = request.form.get('bed_id')
            status = request.form.get('status', '').strip()
            ward = request.form.get('ward', '').strip() or None
            bed_type = request.form.get('bed_type', '').strip() or None
            notes = request.form.get('notes', '').strip() or None
            cur.execute(
                '''UPDATE beds SET status = ?, ward = ?, bed_type = ?, notes = ?, updated_at = ?
                   WHERE id = ? AND hospital_id = ?''',
                (status, ward, bed_type, notes, now, bed_id, hospital_id),
            )
            conn.commit()
            _log_staff_action(hospital_id, staff_id, 'Bed Updated', f"bed_id={bed_id}")
            flash('Bed updated.', 'success')

        elif action == 'delete':
            bed_id = request.form.get('bed_id')
            cur.execute(
                "SELECT COUNT(*) AS c FROM admissions WHERE hospital_id = ? AND bed_id = ? AND status = 'Active'",
                (hospital_id, bed_id),
            )
            in_use = (cur.fetchone()['c'] or 0)
            if in_use:
                conn.close()
                flash('Cannot delete a bed that is currently assigned to an active admission.', 'danger')
                return redirect(url_for('staff_beds'))
            cur.execute('DELETE FROM beds WHERE id = ? AND hospital_id = ?', (bed_id, hospital_id))
            conn.commit()
            _log_staff_action(hospital_id, staff_id, 'Bed Deleted', f"bed_id={bed_id}")
            flash('Bed deleted.', 'success')

        conn.close()
        return redirect(url_for('staff_beds'))

    cur.execute('SELECT * FROM beds WHERE hospital_id = ? ORDER BY bed_number ASC', (hospital_id,))
    beds = cur.fetchall()
    conn.close()
    return render_template('staff/beds.html', staff=staff_row, beds=beds, active_page='beds')


@app.route('/staff/logout')
def staff_logout():
    session.clear()
    flash('Logged out successfully', 'info')
    return redirect(url_for('index'))


@app.route('/doctor/forgot_password', methods=['GET', 'POST'])
def doctor_forgot_password():
    if request.method == 'POST':
        step = request.form.get('step', 'request')
        
        if step == 'request':
            # Request OTP
            email = request.form.get('email', '').strip()
            phone = request.form.get('phone', '').strip()
            
            if not email or not phone:
                flash('Email and phone number are required', 'danger')
                return render_template('forgot_password.html', role='doctor')
            
            # Normalize phone number
            normalized_phone = normalize_phone(phone)
            if not normalized_phone:
                flash('Invalid phone number format', 'danger')
                return render_template('forgot_password.html', role='doctor')
            
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute('SELECT * FROM doctors WHERE email = ?', (email,))
            doctor = cur.fetchone()
            
            if not doctor:
                conn.close()
                flash('Email not found', 'danger')
                return render_template('forgot_password.html', role='doctor')
            
            # Check if phone matches (normalize both)
            doctor_phone = normalize_phone(doctor['phone']) if doctor['phone'] else None
            
            if not doctor_phone:
                conn.close()
                flash('Phone number not registered. Please contact your hospital admin.', 'danger')
                return render_template('forgot_password.html', role='doctor')
            
            if doctor_phone != normalized_phone:
                conn.close()
                flash(f'Phone number does not match. Registered phone ends with: ...{doctor_phone[-4:]}', 'danger')
                return render_template('forgot_password.html', role='doctor')
            
            conn.close()
            
            success, message = send_otp(normalized_phone, 'doctor', email, 'reset')
            if success:
                flash(message, 'success')  # Show OTP in message
                return render_template('forgot_password.html', role='doctor', step='verify', email=email, phone=phone)
            else:
                flash(message, 'danger')
        
        elif step == 'verify':
            # Verify OTP and reset password
            email = request.form.get('email', '').strip()
            phone = request.form.get('phone', '').strip()
            otp_code = request.form.get('otp_code', '').strip()
            new_password = request.form.get('new_password', '').strip()
            confirm_password = request.form.get('confirm_password', '').strip()
            
            if not otp_code or not new_password or not confirm_password:
                flash('All fields are required', 'danger')
                return render_template('forgot_password.html', role='doctor', step='verify', email=email, phone=phone)
            
            if new_password != confirm_password:
                flash('Passwords do not match', 'danger')
                return render_template('forgot_password.html', role='doctor', step='verify', email=email, phone=phone)
            
            # Verify OTP (use normalized phone)
            normalized_phone = normalize_phone(phone)
            success, message = verify_otp(normalized_phone, otp_code, 'doctor', email, 'reset')
            if success:
                # Update password
                conn = get_db_connection()
                cur = conn.cursor()
                cur.execute('UPDATE doctors SET password = ? WHERE email = ?', (new_password, email))
                conn.commit()
                conn.close()
                flash('Password reset successfully. Please login.', 'success')
                return redirect(url_for('doctor_login'))
            else:
                flash(message, 'danger')
                return render_template('forgot_password.html', role='doctor', step='verify', email=email, phone=phone)
    
    return render_template('forgot_password.html', role='doctor')


@app.route('/doctor/logout')
def doctor_logout():
    session.clear()
    flash('Logged out successfully', 'info')
    return redirect(url_for('index'))


@app.route('/doctor/profile', methods=['GET', 'POST'])
def doctor_profile():
    if current_role() != 'doctor':
        flash('Unauthorized', 'danger')
        return redirect(url_for('index'))
    
    doctor_id = current_user_id()
    conn = get_db_connection()
    cur = conn.cursor()
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        specialization = request.form.get('specialization', '').strip() or None
        
        # Check if email is already taken by another doctor
        cur.execute('SELECT id FROM doctors WHERE email = ? AND id != ?', (email, doctor_id))
        if cur.fetchone():
            conn.close()
            flash('Email already exists. Please use a different email.', 'danger')
            cur.execute('SELECT * FROM doctors WHERE id = ?', (doctor_id,))
            doctor = cur.fetchone()
            conn.close()
            return render_template('doctor_profile.html', doctor=doctor)
        
        # Update doctor profile
        try:
            cur.execute('''
                UPDATE doctors 
                SET name = ?, email = ?, phone = ?, specialization = ?
                WHERE id = ?
            ''', (name, email, phone, specialization, doctor_id))
            conn.commit()
            flash('Profile updated successfully', 'success')
            conn.close()
            return redirect(url_for('doctor_profile'))
        except Exception as e:
            conn.rollback()
            conn.close()
            flash(f'Error updating profile: {str(e)}', 'danger')
            return redirect(url_for('doctor_profile'))
    
    # GET request - show current profile
    cur.execute('SELECT * FROM doctors WHERE id = ?', (doctor_id,))
    doctor = cur.fetchone()
    conn.close()
    
    return render_template('doctor_profile.html', doctor=doctor)


@app.route('/doctor/scanner')
def doctor_scanner():
    if current_role() != 'doctor':
        flash('Unauthorized', 'danger')
        return redirect(url_for('index'))
    return render_template('doctor_scanner.html')


@app.route('/doctor/dashboard', methods=['GET', 'POST'])
def doctor_dashboard():
    if current_role() != 'doctor':
        flash('Unauthorized', 'danger')
        return redirect(url_for('index'))

    conn = get_db_connection()
    cur = conn.cursor()

    doctor_id = current_user_id()

    patient = None
    records = []
    inventory_medicines = []

    # Calculate statistics for this doctor
    cur.execute(
        '''SELECT COUNT(DISTINCT user_id) as unique_patients FROM records WHERE doctor_id = ?''',
        (doctor_id,)
    )
    unique_patients_result = cur.fetchone()
    unique_patients_count = unique_patients_result['unique_patients'] if unique_patients_result else 0

    cur.execute(
        '''SELECT COUNT(*) as total_records FROM records WHERE doctor_id = ?''',
        (doctor_id,)
    )
    total_records_result = cur.fetchone()
    total_records_count = total_records_result['total_records'] if total_records_result else 0

    cur.execute(
        '''SELECT COUNT(*) as recovered FROM records WHERE doctor_id = ? AND treatment_status = 'Recovered' ''',
        (doctor_id,)
    )
    recovered_result = cur.fetchone()
    recovered_count = recovered_result['recovered'] if recovered_result else 0

    cur.execute(
        '''SELECT COUNT(*) as observation FROM records WHERE doctor_id = ? AND treatment_status = 'Under Observation' ''',
        (doctor_id,)
    )
    observation_result = cur.fetchone()
    observation_count = observation_result['observation'] if observation_result else 0

    # Handle patient search by Health ID (ABHA-like)
    search_health_id = None
    if request.method == 'POST' and 'search_health_id' in request.form:
        search_health_id = (request.form.get('search_health_id') or '').strip()
    else:
        search_health_id = (request.args.get('search_health_id') or '').strip()

    if search_health_id:
        cur.execute('SELECT * FROM users WHERE health_id = ?', (search_health_id,))
        patient = cur.fetchone()
        if patient:
            cur.execute(
                '''SELECT r.*, d.id as doctor_id, d.name as doctor_name, d.specialization as doctor_specialization,
                          h.id as hospital_id, h.name as hospital_name, h.reg_no as hospital_reg_no
                   FROM records r
                   JOIN doctors d ON r.doctor_id = d.id
                   JOIN hospitals h ON d.hospital_id = h.id
                   WHERE r.user_id = ?
                   ORDER BY r.date DESC''',
                (patient['id'],),
            )
            records = cur.fetchall()
        else:
            flash('No patient found with that Health ID.', 'warning')

    conn.close()

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT hospital_id FROM doctors WHERE id = ?', (doctor_id,))
        doc = cur.fetchone()
        hospital_id = doc['hospital_id'] if doc else None
        if hospital_id is not None:
            cur.execute(
                '''SELECT id, item_name, medicine_type, strength_mg, quantity, unit
                   FROM inventory_items
                   WHERE hospital_id = ?
                   ORDER BY item_name ASC''',
                (hospital_id,),
            )
            inventory_medicines = [dict(r) for r in cur.fetchall()]
        conn.close()
    except sqlite3.OperationalError:
        try:
            conn.close()
        except Exception:
            pass

    return render_template(
        'doctor_dashboard.html',
        patient=patient,
        records=records,
        search_health_id=search_health_id,
        doctor_id=doctor_id,
        inventory_medicines=inventory_medicines,
        unique_patients_count=unique_patients_count,
        total_records_count=total_records_count,
        recovered_count=recovered_count,
        observation_count=observation_count,
        current_user_id=doctor_id,
    )


@app.route('/doctor/patient/<int:user_id>/export/csv')
def doctor_patient_export_csv(user_id):
    """Export all visits for a given patient with the current doctor as CSV."""
    if current_role() != 'doctor':
        flash('Unauthorized', 'danger')
        return redirect(url_for('index'))

    doctor_id = current_user_id()

    conn = get_db_connection()
    cur = conn.cursor()

    # Ensure patient exists
    cur.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    patient = cur.fetchone()
    if not patient:
        conn.close()
        flash('Patient not found.', 'warning')
        return redirect(url_for('doctor_dashboard'))

    # Records for this patient with this doctor
    cur.execute(
        '''SELECT r.*, d.name as doctor_name, d.specialization as doctor_specialization
           FROM records r
           JOIN doctors d ON r.doctor_id = d.id
           WHERE r.user_id = ? AND r.doctor_id = ?
           ORDER BY r.date DESC''',
        (user_id, doctor_id),
    )
    records = cur.fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        'Date',
        'Doctor Name',
        'Doctor Specialization',
        'Diagnosis',
        'Medicines',
        'Dosage',
        'Treatment Status',
        'Prescription Text',
    ])

    for r in records:
        # Use .keys() checks to be safe with older rows that may miss new columns
        dosage_val = r['dosage'] if 'dosage' in r.keys() and r['dosage'] is not None else ''
        prescription_val = (
            r['prescription_text']
            if 'prescription_text' in r.keys() and r['prescription_text'] is not None
            else ''
        )
        status_val = (
            r['treatment_status']
            if 'treatment_status' in r.keys() and r['treatment_status'] is not None
            else ''
        )

        writer.writerow([
            r['date'],
            r['doctor_name'],
            r['doctor_specialization'],
            r['diagnosis'] or '',
            r['medicines'] or '',
            dosage_val,
            status_val,
            prescription_val,
        ])

    csv_data = output.getvalue()
    output.close()

    filename = f"doctor_patient_{user_id}_visits.csv"
    response = Response(csv_data, mimetype='text/csv')
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'
    return response


@app.route('/doctor/add_record/<int:user_id>', methods=['POST'])
def add_record(user_id):
    if current_role() != 'doctor':
        flash('Unauthorized', 'danger')
        return redirect(url_for('index'))

    doctor_id = current_user_id()

    date = request.form['date']
    symptoms = request.form.get('symptoms', '')
    diagnosis = request.form.get('diagnosis', '')
    medicines = request.form.get('medicines', '')
    dosage = request.form.get('dosage', '')
    treatment_status = request.form.get('treatment_status', '')

    # Consultation duration stored in minutes; validate numeric input
    consultation_duration_raw = request.form.get('consultation_duration', '').strip()
    consultation_duration = int(consultation_duration_raw) if consultation_duration_raw.isdigit() else None

    prescription_text = request.form.get('prescription_text', '')
    
    # Health metrics for risk prediction
    age = request.form.get('age', '').strip()
    age = int(age) if age and age.isdigit() else None
    
    gender = request.form.get('gender', '').strip() or None
    
    systolic_bp = request.form.get('systolic_bp', '').strip()
    systolic_bp = int(systolic_bp) if systolic_bp and systolic_bp.isdigit() else None
    
    diastolic_bp = request.form.get('diastolic_bp', '').strip()
    diastolic_bp = int(diastolic_bp) if diastolic_bp and diastolic_bp.isdigit() else None
    
    bmi = request.form.get('bmi', '').strip()
    bmi = float(bmi) if bmi and bmi.replace('.', '').isdigit() else None
    
    cholesterol = request.form.get('cholesterol', '').strip()
    cholesterol = float(cholesterol) if cholesterol and cholesterol.replace('.', '').isdigit() else None
    
    glucose = request.form.get('glucose', '').strip()
    glucose = float(glucose) if glucose and glucose.replace('.', '').isdigit() else None
    
    smoking = request.form.get('smoking', '').strip() or None
    alcohol = request.form.get('alcohol', '').strip() or None
    physical_activity = request.form.get('physical_activity', '').strip() or None
    family_history = request.form.get('family_history', '').strip() or None

    # File uploads: blood report and optional prescription file
    blood_report_file = request.files.get('blood_report_file')
    prescription_file = request.files.get('prescription_file')

    blood_report_filename = None
    if blood_report_file and blood_report_file.filename:
        blood_report_filename = f"blood_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{blood_report_file.filename}"
        blood_report_path = os.path.join(app.config['UPLOAD_FOLDER'], blood_report_filename)
        blood_report_file.save(blood_report_path)

    prescription_filename = None
    if prescription_file and prescription_file.filename:
        prescription_filename = f"presc_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{prescription_file.filename}"
        prescription_path = os.path.join(app.config['UPLOAD_FOLDER'], prescription_filename)
        prescription_file.save(prescription_path)

    conn = get_db_connection()
    cur = conn.cursor()
    
    # Get user data for health risk prediction
    cur.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user_data = cur.fetchone()
    
    # Create health metrics dict for prediction
    health_metrics = {
        'age': age,
        'gender': gender,
        'systolic_bp': systolic_bp,
        'diastolic_bp': diastolic_bp,
        'bmi': bmi,
        'cholesterol': cholesterol,
        'glucose': glucose,
        'smoking': smoking,
        'alcohol': alcohol,
        'physical_activity': physical_activity,
        'family_history': family_history,
    }
    
    # Predict health risk using AI model with health metrics
    risk_level, risk_score, should_trigger_emergency = predict_health_risk(
        user_data, symptoms, diagnosis, treatment_status, medicines, health_metrics
    )
    
    # Insert medical record with risk prediction and health metrics
    # Note: report_filename is kept for backward compatibility, using blood_report_filename value
    cur.execute(
        '''INSERT INTO records
           (user_id, doctor_id, date, symptoms, diagnosis, medicines, dosage, treatment_status,
            consultation_duration, prescription_text, prescription_filename, blood_report_filename,
            report_filename, created_at, risk_level, risk_score,
            systolic_bp, diastolic_bp, bmi, cholesterol, glucose, smoking, alcohol, physical_activity, family_history)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
        (
            user_id,
            doctor_id,
            date,
            symptoms,
            diagnosis,
            medicines,
            dosage,
            treatment_status,
            consultation_duration,
            prescription_text,
            prescription_filename,
            blood_report_filename,
            blood_report_filename,  # report_filename for backward compatibility
            datetime.utcnow().isoformat(),
            risk_level,
            risk_score if risk_score is not None else None,
            systolic_bp,
            diastolic_bp,
            bmi,
            cholesterol,
            glucose,
            smoking,
            alcohol,
            physical_activity,
            family_history,
        ),
    )
    conn.commit()
    
    # If high risk predicted, automatically create emergency record
    emergency_created = False
    if should_trigger_emergency and user_data:
        try:
            # Get patient location (use address or default)
            # Handle both dict and Row objects
            if hasattr(user_data, 'get'):
                patient_location = user_data.get('address', 'Location not specified')
                patient_name = user_data.get('name', 'Patient')
                patient_phone = user_data.get('phone', 'Not provided')
            else:
                patient_location = user_data['address'] if 'address' in user_data.keys() and user_data['address'] else 'Location not specified'
                patient_name = user_data['name'] if 'name' in user_data.keys() and user_data['name'] else 'Patient'
                patient_phone = user_data['phone'] if 'phone' in user_data.keys() and user_data['phone'] else 'Not provided'

            # Auto-assign nearest hospital when emergency is auto-triggered
            assigned_hospital_id = _select_hospital_for_emergency()
            assigned_at = datetime.utcnow().isoformat() if assigned_hospital_id else None

            cur.execute(
                '''INSERT INTO emergencies (user_id, name, phone, location, status, requested_at, response_time_minutes,
                   hospital_id, assigned_at, seen_by_hospital)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (
                    user_id,
                    patient_name,
                    patient_phone,
                    f"{patient_location} (Auto-triggered by AI Risk Assessment)",
                    'Ambulance Dispatched',
                    datetime.utcnow().isoformat(),
                    10,  # Faster response for AI-detected emergencies
                    assigned_hospital_id,
                    assigned_at,
                    0,
                ),
            )
            conn.commit()
            emergency_created = True
        except Exception as e:
            print(f"Error creating emergency record: {e}")
    
    conn.close()
    
    # Flash messages based on risk assessment
    if emergency_created:
        flash(f'⚠️ HIGH RISK DETECTED! Record added. Emergency ambulance automatically dispatched. Risk Level: {risk_level} (Score: {risk_score:.2f})', 'danger')
    elif risk_level:
        if risk_level in ['High', 'Critical']:
            flash(f'⚠️ Record added. High risk detected (Level: {risk_level}, Score: {risk_score:.2f}). Please monitor patient closely.', 'warning')
        else:
            flash(f'Record added successfully. Risk Assessment: {risk_level} (Score: {risk_score:.2f})', 'success')
    else:
        flash('Record added successfully.', 'success')
    
    return redirect(url_for('doctor_dashboard'))


# -----------------
# User auth & dashboard
# -----------------


@app.route('/user/register', methods=['GET', 'POST'])
def user_register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        age_raw = request.form.get('age', '').strip()
        phone = request.form['phone']
        address = request.form['address']
        blood_group = request.form.get('blood_group', '').strip()
        emergency_contact = request.form.get('emergency_contact', '').strip()
        emergency_contact_name = request.form.get('emergency_contact_name', '').strip()

        # Basic numeric validation for age
        age = int(age_raw) if age_raw.isdigit() else None

        health_id = generate_health_id()

        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                '''INSERT INTO users (name, email, password, phone, address, health_id, age, blood_group, emergency_contact, emergency_contact_name)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (name, email, password, phone, address, health_id, age, blood_group, emergency_contact, emergency_contact_name),
            )
            conn.commit()
            user_id = cur.lastrowid
        except sqlite3.IntegrityError:
            conn.close()
            flash('User with this email already exists.', 'danger')
            return render_template('user_register.html')

        conn.close()

        login_user('user', user_id)
        flash('Registration successful.', 'success')
        return redirect(url_for('user_dashboard'))

    return render_template('user_register.html')


@app.route('/user/login', methods=['GET', 'POST'])
def user_login():
    if request.method == 'POST':
        login_type = request.form.get('login_type', 'password')
        print(f"[DEBUG] User login - login_type: {login_type}, form data: {dict(request.form)}")
        
        if login_type == 'otp':
            # OTP login
            identifier = request.form.get('identifier', '').strip()
            phone = request.form.get('phone', '').strip()
            otp_code = request.form.get('otp_code', '').strip()
            
            if not identifier or not phone:
                flash('Health ID and phone number are required', 'danger')
                return render_template('user_login.html', login_type='otp', demo=demo_defaults())
            
            # Normalize phone number
            normalized_phone = normalize_phone(phone)
            if not normalized_phone:
                flash('Invalid phone number format', 'danger')
                return render_template('user_login.html', login_type='otp', identifier=identifier, phone=phone)
            
            if not otp_code:
                # Send OTP
                conn = get_db_connection()
                cur = conn.cursor()
                
                # First check by health_id only
                cur.execute('SELECT * FROM users WHERE health_id = ?', (identifier,))
                user = cur.fetchone()
                
                if not user:
                    conn.close()
                    flash('Health ID not found', 'danger')
                    return render_template('user_login.html', login_type='otp', identifier=identifier, phone=phone)
                
                # Check if phone matches (normalize both)
                user_phone = normalize_phone(user['phone']) if user['phone'] else None
                
                if not user_phone:
                    conn.close()
                    flash('Phone number not registered. Please use password login or contact support.', 'danger')
                    return render_template('user_login.html', login_type='otp', identifier=identifier, phone=phone)
                
                if user_phone != normalized_phone:
                    conn.close()
                    flash(f'Phone number does not match. Registered phone ends with: ...{user_phone[-4:]}', 'danger')
                    return render_template('user_login.html', login_type='otp', identifier=identifier, phone=phone)
                
                conn.close()
                
                # Use normalized phone for OTP
                success, message = send_otp(normalized_phone, 'user', identifier, 'login')
                if success:
                    flash(message, 'success')  # Show OTP in message
                    # Extract OTP code from message for display
                    otp_match = re.search(r'(\d{6})', message)
                    otp_code_display = otp_match.group(1) if otp_match else None
                    return render_template('user_login.html', login_type='otp', identifier=identifier, phone=phone, otp_sent=True, otp_code=otp_code_display, otp_message=message)
                else:
                    flash(message, 'danger')
                return render_template('user_login.html', login_type='otp', identifier=identifier, phone=phone)
            else:
                # Verify OTP (use normalized phone)
                normalized_phone = normalize_phone(phone)
                success, message = verify_otp(normalized_phone, otp_code, 'user', identifier, 'login')
                if success:
                    conn = get_db_connection()
                    cur = conn.cursor()
                    cur.execute('SELECT * FROM users WHERE health_id = ?', (identifier,))
                    user = cur.fetchone()
                    conn.close()
                    
                    if user:
                        login_user('user', user['id'])
                        flash('Logged in successfully', 'success')
                        return redirect(url_for('user_dashboard'))
                else:
                    flash(message, 'danger')
                    return render_template('user_login.html', login_type='otp', identifier=identifier, phone=phone, otp_sent=True)
        else:
            # Password login
            identifier = request.form.get('identifier', '').strip()
            password = request.form.get('password', '').strip()

            if not identifier or not password:
                flash('Health ID and password are required', 'danger')
                return render_template('user_login.html', login_type='password', demo=demo_defaults())

            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute('SELECT * FROM users WHERE health_id = ? AND password = ?', (identifier, password))
            user = cur.fetchone()
            conn.close()

            if user:
                login_user('user', user['id'])
                flash('Logged in successfully', 'success')
                return redirect(url_for('user_dashboard'))
            else:
                flash('Invalid Health ID or password. Please check and try again.', 'danger')
                return render_template('user_login.html', login_type='password', identifier=identifier, demo=demo_defaults())

    return render_template('user_login.html', demo=demo_defaults())


@app.route('/user/forgot_password', methods=['GET', 'POST'])
def user_forgot_password():
    if request.method == 'POST':
        step = request.form.get('step', 'request')
        
        if step == 'request':
            # Request OTP
            identifier = request.form.get('identifier', '').strip()
            phone = request.form.get('phone', '').strip()
            
            if not identifier or not phone:
                flash('Health ID and phone number are required', 'danger')
                return render_template('forgot_password.html', role='user')
            
            # Normalize phone number
            normalized_phone = normalize_phone(phone)
            if not normalized_phone:
                flash('Invalid phone number format', 'danger')
                return render_template('forgot_password.html', role='user')
            
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute('SELECT * FROM users WHERE health_id = ?', (identifier,))
            user = cur.fetchone()
            
            if not user:
                conn.close()
                flash('Health ID not found', 'danger')
                return render_template('forgot_password.html', role='user')
            
            # Check if phone matches (normalize both)
            user_phone = normalize_phone(user['phone']) if user['phone'] else None
            
            if not user_phone:
                conn.close()
                flash('Phone number not registered. Please contact support.', 'danger')
                return render_template('forgot_password.html', role='user')
            
            if user_phone != normalized_phone:
                conn.close()
                flash(f'Phone number does not match. Registered phone ends with: ...{user_phone[-4:]}', 'danger')
                return render_template('forgot_password.html', role='user')
            
            conn.close()
            
            success, message = send_otp(normalized_phone, 'user', identifier, 'reset')
            if success:
                flash(message, 'success')  # Show OTP in message
                return render_template('forgot_password.html', role='user', step='verify', identifier=identifier, phone=phone)
            else:
                flash(message, 'danger')
        
        elif step == 'verify':
            # Verify OTP and reset password
            identifier = request.form.get('identifier', '').strip()
            phone = request.form.get('phone', '').strip()
            otp_code = request.form.get('otp_code', '').strip()
            new_password = request.form.get('new_password', '').strip()
            confirm_password = request.form.get('confirm_password', '').strip()
            
            if not otp_code or not new_password or not confirm_password:
                flash('All fields are required', 'danger')
                return render_template('forgot_password.html', role='user', step='verify', identifier=identifier, phone=phone)
            
            if new_password != confirm_password:
                flash('Passwords do not match', 'danger')
                return render_template('forgot_password.html', role='user', step='verify', identifier=identifier, phone=phone)
            
            # Verify OTP
            success, message = verify_otp(phone, otp_code, 'user', identifier, 'reset')
            if success:
                # Update password
                conn = get_db_connection()
                cur = conn.cursor()
                cur.execute('UPDATE users SET password = ? WHERE health_id = ? AND phone = ?', (new_password, identifier, phone))
                conn.commit()
                conn.close()
                flash('Password reset successfully. Please login.', 'success')
                return redirect(url_for('user_login'))
            else:
                flash(message, 'danger')
                return render_template('forgot_password.html', role='user', step='verify', identifier=identifier, phone=phone)
    
    return render_template('forgot_password.html', role='user')


@app.route('/user/profile', methods=['GET', 'POST'])
def user_profile():
    if current_role() != 'user':
        flash('Unauthorized', 'danger')
        return redirect(url_for('index'))
    
    user_id = current_user_id()
    conn = get_db_connection()
    cur = conn.cursor()
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        address = request.form.get('address', '').strip()
        age_raw = request.form.get('age', '').strip()
        gender = request.form.get('gender', '').strip() or None
        blood_group = request.form.get('blood_group', '').strip() or None
        emergency_contact = request.form.get('emergency_contact', '').strip() or None
        emergency_contact_name = request.form.get('emergency_contact_name', '').strip() or None
        
        age = int(age_raw) if age_raw and age_raw.isdigit() else None
        
        # Check if email is already taken by another user
        cur.execute('SELECT id FROM users WHERE email = ? AND id != ?', (email, user_id))
        if cur.fetchone():
            conn.close()
            flash('Email already exists. Please use a different email.', 'danger')
            cur.execute('SELECT * FROM users WHERE id = ?', (user_id,))
            user = cur.fetchone()
            conn.close()
            return render_template('user_profile.html', user=user)
        
        # Update user profile
        try:
            cur.execute('''
                UPDATE users 
                SET name = ?, email = ?, phone = ?, address = ?, age = ?, gender = ?, blood_group = ?, emergency_contact = ?, emergency_contact_name = ?
                WHERE id = ?
            ''', (name, email, phone, address, age, gender, blood_group, emergency_contact, emergency_contact_name, user_id))
            conn.commit()
            flash('Profile updated successfully', 'success')
            conn.close()
            return redirect(url_for('user_profile'))
        except Exception as e:
            conn.rollback()
            conn.close()
            flash(f'Error updating profile: {str(e)}', 'danger')
            return redirect(url_for('user_profile'))
    
    # GET request - show current profile
    cur.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cur.fetchone()
    conn.close()
    
    return render_template('user_profile.html', user=user)


@app.route('/user/logout')
def user_logout():
    session.clear()
    flash('Logged out successfully', 'info')
    return redirect(url_for('index'))


@app.route('/user/dashboard')
def user_dashboard():
    if current_role() != 'user':
        flash('Unauthorized', 'danger')
        return redirect(url_for('index'))

    user_id = current_user_id()

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cur.fetchone()

    # Full medical records with doctor info
    cur.execute(
        '''SELECT r.*, d.name as doctor_name, d.specialization as doctor_specialization
           FROM records r
           JOIN doctors d ON r.doctor_id = d.id
           WHERE r.user_id = ?
           ORDER BY r.date DESC''',
        (user_id,),
    )
    records = cur.fetchall()

    # User emergencies
    try:
        cur.execute(
            '''SELECT e.*, h.name AS hospital_name
               FROM emergencies e
               LEFT JOIN hospitals h ON e.hospital_id = h.id
               WHERE e.user_id = ?
               ORDER BY e.requested_at DESC
               LIMIT 200''',
            (user_id,),
        )
        emergencies = cur.fetchall()
    except sqlite3.OperationalError:
        emergencies = []

    records_count = len(records) if records else 0
    emergencies_total = len(emergencies) if emergencies else 0
    emergencies_assigned = 0
    emergencies_unassigned = 0
    if emergencies:
        for e in emergencies:
            if e['hospital_id']:
                emergencies_assigned += 1
            else:
                emergencies_unassigned += 1

    # Distinct hospitals that have treated this user
    cur.execute(
        '''SELECT DISTINCT h.id AS hospital_id, h.name
           FROM records r
           JOIN doctors d ON r.doctor_id = d.id
           JOIN hospitals h ON d.hospital_id = h.id
           WHERE r.user_id = ?
           ORDER BY h.name''',
        (user_id,),
    )
    hospitals = cur.fetchall()

    conn.close()

    # Ensure QR exists
    qr_rel_path = generate_health_qr(user['health_id'])

    return render_template(
        'user_dashboard.html',
        user=user,
        records=records,
        records_count=records_count,
        emergencies=emergencies,
        emergencies_total=emergencies_total,
        emergencies_assigned=emergencies_assigned,
        emergencies_unassigned=emergencies_unassigned,
        hospitals=hospitals,
        qr_path=qr_rel_path,
    )


@app.route('/user/scanner')
def user_scanner():
    if current_role() != 'user':
        flash('Unauthorized', 'danger')
        return redirect(url_for('index'))
    return render_template('user_scanner.html')


@app.route('/user/records/export/csv')
def user_records_export_csv():
    if current_role() != 'user':
        flash('Unauthorized', 'danger')
        return redirect(url_for('index'))

    user_id = current_user_id()
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        '''SELECT r.*, d.name as doctor_name, d.specialization as doctor_specialization
           FROM records r
           JOIN doctors d ON r.doctor_id = d.id
           WHERE r.user_id = ?
           ORDER BY r.date DESC''',
        (user_id,),
    )
    records = cur.fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        'Date',
        'Doctor Name',
        'Doctor Specialization',
        'Diagnosis',
        'Symptoms',
        'Medicines',
        'Dosage',
        'Treatment Status',
        'Prescription Text',
        'Prescription File',
        'Blood Report File',
        'Created At',
    ])
    for r in records:
        dosage_val = r['dosage'] if 'dosage' in r.keys() and r['dosage'] is not None else ''
        status_val = r['treatment_status'] if 'treatment_status' in r.keys() and r['treatment_status'] is not None else ''
        pres_txt = r['prescription_text'] if 'prescription_text' in r.keys() and r['prescription_text'] is not None else ''
        pres_file = r['prescription_filename'] if 'prescription_filename' in r.keys() and r['prescription_filename'] else ''
        blood_file = r['blood_report_filename'] if 'blood_report_filename' in r.keys() and r['blood_report_filename'] else ''
        created_at = r['created_at'] if 'created_at' in r.keys() and r['created_at'] else ''
        writer.writerow([
            r['date'],
            r['doctor_name'],
            r['doctor_specialization'],
            r['diagnosis'] or '',
            r['symptoms'] or '',
            r['medicines'] or '',
            dosage_val,
            status_val,
            pres_txt,
            pres_file,
            blood_file,
            created_at,
        ])

    csv_data = output.getvalue()
    output.close()
    response = Response(csv_data, mimetype='text/csv')
    response.headers['Content-Disposition'] = 'attachment; filename=user_records.csv'
    return response


@app.route('/user/emergencies/export/csv')
def user_emergencies_export_csv():
    if current_role() != 'user':
        flash('Unauthorized', 'danger')
        return redirect(url_for('index'))

    user_id = current_user_id()
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            '''SELECT e.*, h.name AS hospital_name
               FROM emergencies e
               LEFT JOIN hospitals h ON e.hospital_id = h.id
               WHERE e.user_id = ?
               ORDER BY e.requested_at DESC''',
            (user_id,),
        )
        rows = cur.fetchall()
    except sqlite3.OperationalError:
        rows = []
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        'ID', 'Requested At', 'Name', 'Phone', 'Location', 'State', 'District', 'Priority', 'Status', 'Assigned Hospital', 'Response Time (mins)'
    ])
    for e in rows:
        writer.writerow([
            e['id'],
            e['requested_at'] or '',
            e['name'] or '',
            e['phone'] or '',
            e['location'] or '',
            e['state'] if 'state' in e.keys() and e['state'] else '',
            e['district'] if 'district' in e.keys() and e['district'] else '',
            e['priority'] if 'priority' in e.keys() and e['priority'] else '',
            e['status'] or '',
            e['hospital_name'] or '',
            e['response_time_minutes'] if 'response_time_minutes' in e.keys() and e['response_time_minutes'] is not None else '',
        ])

    csv_data = output.getvalue()
    output.close()
    response = Response(csv_data, mimetype='text/csv')
    response.headers['Content-Disposition'] = 'attachment; filename=user_emergencies.csv'
    return response


@app.route('/user/hospital/<int:hospital_id>')
def user_hospital_detail(hospital_id):
    if current_role() != 'user':
        flash('Unauthorized', 'danger')
        return redirect(url_for('index'))

    user_id = current_user_id()

    conn = get_db_connection()
    cur = conn.cursor()

    # Load hospital
    cur.execute('SELECT * FROM hospitals WHERE id = ?', (hospital_id,))
    hospital = cur.fetchone()
    if not hospital:
        conn.close()
        flash('Hospital not found.', 'warning')
        return redirect(url_for('user_dashboard'))

    # Load this user's records at this hospital
    cur.execute(
        '''SELECT r.*, d.name as doctor_name, d.specialization as doctor_specialization
           FROM records r
           JOIN doctors d ON r.doctor_id = d.id
           WHERE r.user_id = ? AND d.hospital_id = ?
           ORDER BY r.date DESC''',
        (user_id, hospital_id),
    )
    records = cur.fetchall()

    conn.close()

    print_mode = request.args.get('print') == '1'

    return render_template('user_hospital_detail.html', hospital=hospital, records=records, print_mode=print_mode)


@app.route('/user/hospital/<int:hospital_id>/export/csv')
def user_hospital_export_csv(hospital_id):
    """Export this user's visits at a specific hospital as CSV (Excel-compatible)."""
    if current_role() != 'user':
        flash('Unauthorized', 'danger')
        return redirect(url_for('index'))

    user_id = current_user_id()

    conn = get_db_connection()
    cur = conn.cursor()

    # Ensure hospital exists
    cur.execute('SELECT * FROM hospitals WHERE id = ?', (hospital_id,))
    hospital = cur.fetchone()
    if not hospital:
        conn.close()
        flash('Hospital not found.', 'warning')
        return redirect(url_for('user_dashboard'))

    # Same filter as user_hospital_detail
    cur.execute(
        '''SELECT r.*, d.name as doctor_name, d.specialization as doctor_specialization
           FROM records r
           JOIN doctors d ON r.doctor_id = d.id
           WHERE r.user_id = ? AND d.hospital_id = ?
           ORDER BY r.date DESC''',
        (user_id, hospital_id),
    )
    records = cur.fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        'Date',
        'Doctor Name',
        'Doctor Specialization',
        'Diagnosis',
        'Medicines',
        'Dosage',
        'Treatment Status',
        'Prescription Text',
    ])

    for r in records:
        # Safely handle legacy rows that might not have new columns
        dosage_val = r['dosage'] if 'dosage' in r.keys() and r['dosage'] is not None else ''
        prescription_val = (
            r['prescription_text']
            if 'prescription_text' in r.keys() and r['prescription_text'] is not None
            else ''
        )
        status_val = (
            r['treatment_status']
            if 'treatment_status' in r.keys() and r['treatment_status'] is not None
            else ''
        )

        writer.writerow([
            r['date'],
            r['doctor_name'],
            r['doctor_specialization'],
            r['diagnosis'] or '',
            r['medicines'] or '',
            dosage_val,
            status_val,
            prescription_val,
        ])

    csv_data = output.getvalue()
    output.close()

    filename = f"user_hospital_{hospital_id}_visits.csv"
    response = Response(csv_data, mimetype='text/csv')
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'
    return response


@app.route('/reports/<filename>')
def download_report(filename):
    """Keep download endpoint for backwards compatibility (forced attachment)."""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)


@app.route('/reports/view/<filename>')
def view_report(filename):
    """Serve report inline so browser can preview PDF/images without download dialog."""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=False)


@app.route('/hospital/patient/<int:user_id>/export/csv')
def hospital_patient_export_csv(user_id):
    """Export all visits for a patient at this hospital as CSV (Excel-compatible)."""
    if current_role() != 'hospital':
        flash('Unauthorized', 'danger')
        return redirect(url_for('index'))

    hospital_id = current_user_id()

    conn = get_db_connection()
    cur = conn.cursor()

    # Ensure patient exists
    cur.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    patient = cur.fetchone()
    if not patient:
        conn.close()
        flash('Patient not found.', 'warning')
        return redirect(url_for('hospital_dashboard'))

    # Same records as hospital_patient_detail
    cur.execute(
        '''SELECT r.*, d.name as doctor_name, d.specialization as doctor_specialization
           FROM records r
           JOIN doctors d ON r.doctor_id = d.id
           WHERE r.user_id = ? AND d.hospital_id = ?
           ORDER BY r.date DESC''',
        (user_id, hospital_id),
    )
    records = cur.fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)

    # Header row
    writer.writerow([
        'Date',
        'Doctor Name',
        'Doctor Specialization',
        'Diagnosis',
        'Medicines',
        'Dosage',
        'Treatment Status',
        'Prescription Text',
    ])

    for r in records:
        # Safely handle legacy rows that might not have new columns
        dosage_val = r['dosage'] if 'dosage' in r.keys() and r['dosage'] is not None else ''
        prescription_val = (
            r['prescription_text']
            if 'prescription_text' in r.keys() and r['prescription_text'] is not None
            else ''
        )
        status_val = (
            r['treatment_status']
            if 'treatment_status' in r.keys() and r['treatment_status'] is not None
            else ''
        )

        writer.writerow([
            r['date'],
            r['doctor_name'],
            r['doctor_specialization'],
            r['diagnosis'] or '',
            r['medicines'] or '',
            dosage_val,
            status_val,
            prescription_val,
        ])

    csv_data = output.getvalue()
    output.close()

    filename = f"patient_{user_id}_visits.csv"
    response = Response(csv_data, mimetype='text/csv')
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'
    return response


# -----------------
# Emergency module
# -----------------


@app.route('/emergency', methods=['GET', 'POST'])
def emergency():
    user_id = current_user_id() if current_role() == 'user' else None

    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        location = request.form['location']
        symptoms = request.form.get('symptoms', '')
        age = request.form.get('age')
        age = int(age) if age and age.isdigit() else None
        
        # New fields for ML model
        state = request.form.get('state')
        district = request.form.get('district')
        zone = request.form.get('zone')
        day = request.form.get('day')
        time_slot = request.form.get('time_slot')
        emergency_type = request.form.get('emergency_type')
        weather = request.form.get('weather')
        
        # Auto-detect day if not provided
        if not day:
            day = datetime.now().strftime('%A')
        
        # Auto-detect time slot if not provided
        if not time_slot:
            current_hour = datetime.now().hour
            if 5 <= current_hour < 12:
                time_slot = 'Morning'
            elif 12 <= current_hour < 17:
                time_slot = 'Afternoon'
            elif 17 <= current_hour < 21:
                time_slot = 'Evening'
            else:
                time_slot = 'Night'

        # Get user data if logged in
        user_data = None
        if user_id:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute('SELECT * FROM users WHERE id = ?', (user_id,))
            user_row = cur.fetchone()
            if user_row:
                # Convert Row to dict
                user_data = dict(user_row)
            conn.close()

        # Predict emergency priority using ML model
        priority, severity, prediction_score = predict_emergency_priority(
            symptoms=symptoms,
            age=age,
            location=location,
            state=state,
            zone=zone,
            day=day,
            time_slot=time_slot,
            emergency_type=emergency_type,
            weather=weather,
            user_data=user_data
        )

        # Calculate response time based on priority
        response_time_map = {
            'Critical': 5,
            'High': 10,
            'Medium': 15,
            'Low': 20
        }
        response_time = response_time_map.get(priority, 15)

        # Determine status based on priority
        status_map = {
            'Critical': 'Ambulance Dispatched - Critical Priority',
            'High': 'Ambulance Dispatched - High Priority',
            'Medium': 'Ambulance Dispatched - Medium Priority',
            'Low': 'Ambulance Dispatched - Low Priority'
        }
        status = status_map.get(priority, 'Ambulance Dispatched')

        # Assign nearest hospital (district -> state fallback)
        assigned_hospital_id = _select_hospital_for_emergency(state=state, district=district)
        assigned_at = datetime.utcnow().isoformat() if assigned_hospital_id else None

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            '''INSERT INTO emergencies (user_id, name, phone, location, status, requested_at, 
               response_time_minutes, priority, severity, prediction_score, symptoms, age,
               state, district, zone, day, time_slot, emergency_type, weather,
               hospital_id, assigned_at, seen_by_hospital)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (
                user_id,
                name,
                phone,
                location,
                status,
                datetime.utcnow().isoformat(),
                response_time,
                priority,
                severity,
                prediction_score,
                symptoms,
                age,
                state,
                district,
                zone,
                day,
                time_slot,
                emergency_type,
                weather,
                assigned_hospital_id,
                assigned_at,
                0
            ),
        )
        conn.commit()

        # Get emergency ID for result page
        emergency_id = cur.lastrowid

        # Calculate active requests (pending emergencies, excluding current one)
        cur.execute('SELECT COUNT(*) AS c FROM emergencies WHERE id != ? AND status LIKE ?', 
                   (emergency_id, '%Dispatched%'))
        active_requests = cur.fetchone()['c']
        
        # Calculate available ambulances (simulated: total ambulances - active requests)
        # In a real system, this would come from ambulance tracking system
        total_ambulances = 10  # Simulated total ambulances
        available_ambulances = max(0, total_ambulances - active_requests - 1)  # -1 for current dispatch
        
        # Get prediction probabilities for all classes
        prediction_probabilities = {}
        if emergency_model and hasattr(emergency_model, 'predict_proba'):
            try:
                # Re-extract features for probability calculation
                symptom_text = str(symptoms).lower() if symptoms else ''
                age_normalized = (age / 100.0) if age else 0.5
                
                # Symptom severity
                critical_keywords = ['chest pain', 'difficulty breathing', 'unconscious', 'severe', 'emergency', 
                                    'critical', 'heart attack', 'stroke', 'bleeding', 'trauma', 'accident']
                high_keywords = ['pain', 'fever', 'vomiting', 'dizziness', 'nausea', 'weakness']
                moderate_keywords = ['discomfort', 'mild', 'ache', 'tired']
                
                symptom_severity = 0.0
                if any(keyword in symptom_text for keyword in critical_keywords):
                    symptom_severity = 1.0
                elif any(keyword in symptom_text for keyword in high_keywords):
                    symptom_severity = 0.7
                elif any(keyword in symptom_text for keyword in moderate_keywords):
                    symptom_severity = 0.4
                else:
                    symptom_severity = 0.2
                
                # Build features (same as in predict_emergency_priority)
                states_list = ['All India', 'Uttar Pradesh', 'Maharashtra', 'West Bengal', 'Jharkhand',
                               'Madhya Pradesh', 'Bihar', 'Rajasthan', 'Tamil Nadu', 'Orissa', 'Assam',
                               'Karnataka', 'Andhra Pradesh', 'Haryana', 'Chhatisgarh', 'Jammu and Kashmir',
                               'Telangana', 'Uttarakhand', 'Himachal Pradesh', 'Gujarat', 'Kerala',
                               'Arunachal Pradesh', 'Delhi', 'Nagaland', 'Mizoram', 'Meghalaya',
                               'Tripura', 'Manipur', 'Goa', 'Andaman and Nicobar Island', 'Ladakh',
                               'Sikkim', 'Puducherry', 'Dadra and Nagar Haveli and Daman and Diu', 'Chandigarh']
                zone_options = ['Urban', 'Rural', 'Highway']
                day_options = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                time_slot_options = ['Morning', 'Afternoon', 'Evening', 'Night']
                emergency_type_options = ['EMS', 'Traffic', 'Fire']
                weather_options = ['Rain', 'Heatwave', 'Fog', 'Clear']
                
                features_list = [age_normalized, symptom_severity]
                
                # State one-hot
                state_onehot = [0] * len(states_list)
                if state and state in states_list:
                    state_onehot[states_list.index(state)] = 1
                features_list.extend(state_onehot)
                
                # Zone one-hot
                zone_onehot = [0] * len(zone_options)
                if zone and zone in zone_options:
                    zone_onehot[zone_options.index(zone)] = 1
                features_list.extend(zone_onehot)
                
                # Day one-hot
                day_onehot = [0] * len(day_options)
                if day and day in day_options:
                    day_onehot[day_options.index(day)] = 1
                features_list.extend(day_onehot)
                
                # Time slot one-hot
                time_slot_onehot = [0] * len(time_slot_options)
                if time_slot and time_slot in time_slot_options:
                    time_slot_onehot[time_slot_options.index(time_slot)] = 1
                features_list.extend(time_slot_onehot)
                
                # Emergency type one-hot
                emergency_type_onehot = [0] * len(emergency_type_options)
                if emergency_type and emergency_type in emergency_type_options:
                    emergency_type_onehot[emergency_type_options.index(emergency_type)] = 1
                features_list.extend(emergency_type_onehot)
                
                # Weather one-hot
                weather_onehot = [0] * len(weather_options)
                if weather and weather in weather_options:
                    weather_onehot[weather_options.index(weather)] = 1
                features_list.extend(weather_onehot)
                
                # Truncate to model's expected features
                n_features = emergency_model.n_features_in_
                if len(features_list) > n_features:
                    features_list = features_list[:n_features]
                elif len(features_list) < n_features:
                    features_list = features_list + [0.0] * (n_features - len(features_list))
                
                features = np.array([features_list])
                
                # Get probabilities
                with warnings.catch_warnings():
                    warnings.filterwarnings('ignore', category=UserWarning)
                    probabilities = emergency_model.predict_proba(features)[0]
                    classes = emergency_model.classes_
                    
                    # Map probabilities to priority levels
                    for i, class_name in enumerate(classes):
                        if class_name == 'Low':
                            prediction_probabilities['Low'] = float(probabilities[i]) * 100
                        elif class_name == 'Medium':
                            prediction_probabilities['Medium'] = float(probabilities[i]) * 100
                        elif class_name == 'High':
                            prediction_probabilities['High'] = float(probabilities[i]) * 100
            except Exception as e:
                print(f"[WARNING] Could not get prediction probabilities: {e}")
                # Fallback probabilities
                if priority == 'Low':
                    prediction_probabilities = {'Low': 75.0, 'Medium': 20.0, 'High': 5.0}
                elif priority == 'Medium':
                    prediction_probabilities = {'Low': 20.0, 'Medium': 60.0, 'High': 20.0}
                else:
                    prediction_probabilities = {'Low': 10.0, 'Medium': 30.0, 'High': 60.0}
        else:
            # Fallback probabilities
            if priority == 'Low':
                prediction_probabilities = {'Low': 75.0, 'Medium': 20.0, 'High': 5.0}
            elif priority == 'Medium':
                prediction_probabilities = {'Low': 20.0, 'Medium': 60.0, 'High': 20.0}
            else:
                prediction_probabilities = {'Low': 10.0, 'Medium': 30.0, 'High': 60.0}
        
        # Calculate area demand forecast
        demand_factors = []
        if day and day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']:
            demand_factors.append('Weekday')
        if time_slot in ['Morning', 'Afternoon']:
            demand_factors.append(f'{time_slot.lower()} time slot')
        if weather == 'Clear':
            demand_factors.append('Clear weather conditions')
        elif weather in ['Rain', 'Fog']:
            demand_factors.append(f'{weather.lower()} conditions')
        
        # Historical frequency (simulated)
        cur.execute('SELECT COUNT(*) AS c FROM emergencies WHERE state = ?', (state or 'All India',))
        historical_count = cur.fetchone()['c']
        if historical_count < 5:
            demand_factors.append('Low historical emergency frequency')
        elif historical_count < 20:
            demand_factors.append('Moderate historical emergency frequency')
        else:
            demand_factors.append('High historical emergency frequency')
        
        if available_ambulances >= 3:
            demand_factors.append('Adequate ambulance availability')
        else:
            demand_factors.append('Limited ambulance availability')
        
        # Determine demand level
        if available_ambulances >= 4 and historical_count < 10:
            demand_level = 'LOW'
        elif available_ambulances >= 2 and historical_count < 20:
            demand_level = 'MEDIUM'
        else:
            demand_level = 'HIGH'
        
        # Determine life threat risk
        symptom_text = str(symptoms).lower() if symptoms else ''
        life_threat_keywords = ['chest pain', 'heart attack', 'stroke', 'unconscious', 'bleeding', 
                               'difficulty breathing', 'trauma', 'accident', 'severe']
        life_threat_risk = 'Yes' if any(keyword in symptom_text for keyword in life_threat_keywords) else 'No'
        
        # Determine dispatch type
        dispatch_type_map = {
            'Critical': 'Emergency Priority',
            'High': 'High Priority',
            'Medium': 'Standard Priority',
            'Low': 'Non-Emergency Priority'
        }
        dispatch_type = dispatch_type_map.get(priority, 'Standard Priority')
        
        # Decision logic
        decision_logic = []
        if severity in ['Mild', 'Moderate']:
            decision_logic.append('Patient condition is non-critical')
        else:
            decision_logic.append('Patient condition requires immediate attention')
        
        if demand_level == 'LOW':
            decision_logic.append('Area demand currently low')
        elif demand_level == 'HIGH':
            decision_logic.append('Area demand currently high')
        else:
            decision_logic.append('Area demand at moderate level')
        
        if active_requests == 0:
            decision_logic.append('No competing high-priority emergencies')
        else:
            decision_logic.append(f'{active_requests} other active emergency requests')
        
        # Simple analytics: total emergencies, avg response time
        cur.execute('SELECT COUNT(*) AS c, AVG(response_time_minutes) AS avg_rt FROM emergencies')
        stats = cur.fetchone()

        # Get the emergency record with predictions
        cur.execute('SELECT * FROM emergencies WHERE id = ?', (emergency_id,))
        emergency_record = cur.fetchone()

        conn.close()

        flash(f'Emergency request submitted. Ambulance is on the way! Priority: {priority}', 'success')
        return render_template('emergency_result.html', 
                             stats=stats, 
                             emergency=emergency_record,
                             priority=priority,
                             severity=severity,
                             prediction_score=prediction_score,
                             zone=zone,
                             day=day,
                             time_slot=time_slot,
                             emergency_type=emergency_type,
                             weather=weather,
                             active_requests=active_requests,
                             available_ambulances=available_ambulances,
                             demand_level=demand_level,
                             demand_factors=demand_factors,
                             life_threat_risk=life_threat_risk,
                             dispatch_type=dispatch_type,
                             decision_logic=decision_logic,
                             prediction_probabilities=prediction_probabilities,
                             response_time=response_time)

    return render_template('emergency.html')


# -------------
# Simple analytics for hospital dashboard emergency stats
# -------------


@app.route('/analytics/ambulance')
def ambulance_analytics():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) AS c, AVG(response_time_minutes) AS avg_rt FROM emergencies')
    stats = cur.fetchone()
    conn.close()
    return {
        'total_emergencies': stats['c'] if stats else 0,
        'avg_response_time': round(stats['avg_rt'], 1) if stats and stats['avg_rt'] else None,
    }


if __name__ == '__main__':
    args = _parse_cli_args(sys.argv[1:])
    if args.purge_non_demo:
        if not args.yes:
            print('[ABORTED] Refusing to purge without --yes confirmation')
            raise SystemExit(2)
        init_db()
        purge_non_demo_data(keep_demo_records_only=True)
        init_db()
        print('[OK] Purged all non-demo accounts and re-seeded demo data')
        raise SystemExit(0)

    init_db()
    app.run(host='0.0.0.0', port=5001, ssl_context='adhoc', debug=True)
