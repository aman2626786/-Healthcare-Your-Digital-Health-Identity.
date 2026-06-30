# Healthcare - Emergency Response Data Management System
Live Demo: https://healthcare-your-digital-health-identity-1.onrender.com/

A multi-role healthcare platform for emergency-ready care coordination across patients, doctors, hospitals, staff, and central health admins.

## Overview
Healthcare solves critical problems in emergency and routine care:

- Fast patient identification with QR-based Health ID
- Privacy-safe public emergency access with role-based full access for doctors
- Trusted hospital verification using hospital QR pages
- AI-assisted emergency and risk prioritization
- Hospital operations management (inventory, beds, staff, admissions, emergencies)
- Automation-ready chatbot workflow through n8n

---

## Problem Statement
In emergency situations, patient data access and provider trust verification are often delayed or unreliable.  
Healthcare addresses this by implementing a QR-first architecture where:

- Public users can access only limited emergency patient information
- Doctors can access complete medical records when authorized
- Patients can verify whether a hospital is trusted/ABHA-connected through hospital verification QR

This reduces treatment delays, helps avoid untrusted providers, and improves decision safety.

---

## Key Features

### 1. Multi-Role Access
- User/Patient panel
- Doctor panel
- Hospital admin panel
- Staff panel
- Health admin panel

Each panel has role-specific routes, dashboards, and data permissions.

### 2. Intelligent QR Ecosystem
- Patient Health ID QR generation
- Public emergency card access via `/scan/<health_id>`
- Doctor full-record access from same scan flow
- Doctor scanner support and health ID-based patient lookup
- Hospital verification QR via `/hospital/verify/<reg_no>`

### 3. Hospital Trust Verification (New)
- Hospitals now get a public verification URL and QR
- Patients can confirm hospital registration details and ABHA-connected status
- Improves trust and reduces fake/unverified provider risk

### 4. Emergency Response System
- Emergency request intake
- AI/rule-based emergency priority and severity scoring
- Emergency assignment to hospitals
- Hospital emergency status management
- Response-time analytics and exports

### 5. Medical Records Management
- Doctors create and update treatment records
- Symptoms, diagnosis, medicines, dosage, treatment status, prescription notes/files
- User and doctor-level CSV export support

### 6. Hospital Operations
- Doctor account management
- Inventory management
- Bed management
- Staff management
- Admissions and discharges
- Staff tasks and activity logs

### 7. Analytics and Reporting
- Dashboard charts (status, priority, operational counts)
- CSV exports for emergency and medical workflows
- Lightweight ambulance analytics endpoint

### 8. OTP and Authentication Support
- Password and OTP-based flows for user types
- Firebase-ready OTP integration
- Database-backed OTP lifecycle management

---

## Role-wise Functional Summary

### User/Patient
- Register, login, update profile
- Maintain blood group and emergency contact
- Get Health ID and QR
- Use scanner to read patient/hospital QR targets
- View own treatment history hospital-wise
- Trigger emergency request
- Export records/emergency history

### Doctor
- Login/profile
- Scan patient QR or search by Health ID
- View full patient medical history
- Add diagnosis and treatment entries
- Export patient records

### Hospital Admin
- Register/login/profile
- Manage doctors
- Monitor emergencies and assign/update status
- Manage inventory, beds, staff, and operational data
- Access hospital verification QR and public verify link

### Staff
- Dashboard for tasks and operational actions
- Patient status updates
- Medicine administration tracking
- Bed/admission workflows
- Staff activity logging

### Health Admin
- System-wide hospital oversight
- Hospital detail and management
- Emergency assignment and monitoring
- Data export tools

---

## Architecture

### Backend
- Flask monolith (`backend/app.py`)
- Role-based route guards via session checks
- SQLite as primary relational store
- QR generation utility methods
- ML model loading and inference with fallbacks

### Frontend
- Jinja2 templates (`frontend/templates`)
- Vanilla JS interaction layer (`frontend/static/app.js`)
- Theme and responsive UI in CSS (`frontend/static/style.css`)
- Scanner integration with `html5-qrcode`
- Charts via Chart.js

### Data Layer
Primary tables:
- `users`, `doctors`, `hospitals`, `records`, `emergencies`, `otp_codes`
- `health_admins`, `inventory_items`, `staff`, `staff_tasks`, `staff_activity_log`
- `patient_status`, `medicine_administration`, `beds`, `admissions`

---

## AI/ML Components

### Health Risk Prediction
- SVM-based model (`svm_health_risk_model.pkl`)
- Predicts risk level and trigger intent for emergency escalation
- Includes robust fallback logic

### Emergency Priority Prediction
- Logistic Regression model (`Logistic_regression_prediction.pkl`)
- Outputs priority/severity score path
- Rule-based fallback if model unavailable or incompatible

---

## Automation with n8n

The chatbot is integrated with an n8n webhook workflow:

- Frontend sends `sessionId`, `chatInput`, and `message` to n8n webhook
- n8n can orchestrate automation logic and AI responses
- Session continuity is maintained via browser localStorage
- Multiple response payload styles are handled (`output`, `text`, `response`, etc.)
- Graceful error handling is shown if n8n workflow is offline

File reference:
- `frontend/static/chatbot.js`

---

## Tech Stack

### Core
- Python 3
- Flask
- SQLite
- HTML, CSS, JavaScript (Vanilla)

### Libraries/Tools
- `qrcode` for QR generation
- `numpy`, `pickle`, `joblib`, `dill` for ML loading/inference
- Firebase Admin SDK (optional OTP integration path)
- `html5-qrcode` for camera scanner
- Chart.js for data visualization

### Deployment/Runtime
- `run.py` (local app launcher)
- `wsgi.py` (WSGI entrypoint)
- Gunicorn-ready
- Docker and docker-compose support

---

## Important Routes (Selected)
- `/` - Home
- `/scan/<health_id>` - Patient QR scan endpoint
- `/doctor/scan_result/<health_id>` - Doctor full-access scan result
- `/hospital/verify/<reg_no>` - Public hospital verification page
- `/emergency` - Emergency request workflow
- `/analytics/ambulance` - Emergency analytics endpoint

Full route list:
- `backend/routes.txt`

---

## Local Setup

```bash
pip install -r requirements.txt
python run.py
```

App typically runs on:
- `http://localhost:5000` (via `run.py`)

Note:
- Keep `USE_HTTPS=0` for local development if you want to avoid local certificate warnings.

---

## Configuration

Environment-driven settings are supported through `env.example` and `backend/config.py`.

Key configurable areas:
- Host and port
- Debug mode
- Database path
- OTP settings
- Upload and QR folders
- Firebase credentials/API key
- HTTPS toggle for local run mode

---

## Project Structure

```text
backend/
  app.py
  config.py
  health_system.db
  pkl/
  uploads/
  routes.txt
  schema.txt

frontend/
  templates/
  static/

run.py
wsgi.py
requirements.txt
Dockerfile
docker-compose.yml
```

---

## Current Branding and UI State
- Product name: **Healthcare**
- Updated UI theme with healthcare-focused palette
- Light/Dark mode retained
- Scanner and trust-verification flows integrated in UX

---

## Future Extension Ideas
- API documentation (OpenAPI-style)
- ER diagram for DB schema
- Dedicated n8n workflow export and setup guide
- Notification integrations (SMS/WhatsApp/email)
- Production hardening checklist

