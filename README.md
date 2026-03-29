# Swasthya Sampark - Healthcare Management System

A comprehensive healthcare management system with AI-powered emergency response.

DEMO = https://swasthya-sampark-0tds.onrender.com/

## Project Structure

```
vgu/
├── backend/          # Backend application (Flask, Python)
│   ├── app.py       # Main Flask application
│   ├── config.py    # Configuration management
│   ├── health_system.db  # SQLite database
│   ├── pkl/         # Machine learning models
│   ├── uploads/     # Uploaded files
│   ├── *.py         # Python scripts (training, testing)
│   └── *.md         # Documentation files
│
├── frontend/         # Frontend application (HTML, CSS, JS)
│   ├── templates/   # HTML templates (Jinja2)
│   └── static/      # Static assets (CSS, JS, images)
│
├── README.md        # Project documentation
├── QUICKSTART.md    # Quick start guide
├── DEPLOYMENT.md    # Deployment instructions
├── requirements.txt # Python dependencies
├── wsgi.py          # WSGI entry point
├── Dockerfile       # Docker configuration
├── docker-compose.yml # Docker Compose configuration
└── run.py           # Application launcher
```

## Quick Start

**New to the project?** See [QUICKSTART.md](QUICKSTART.md) for a step-by-step guide.

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the application
python run.py
```

The application will be available at `http://localhost:5000`

## Running the Application

### Development Mode (Recommended for first-time setup)
```bash
python run.py
```

### Production Mode
```bash
# Using Gunicorn
gunicorn --config gunicorn_config.py wsgi:application

# Using Docker
docker-compose up -d
```

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions.

## Features

- **User Management**: Patient registration, login, profile management
- **Doctor Dashboard**: Medical record management, AI risk assessment
- **Hospital Dashboard**: Patient management, analytics
- **Emergency System**: AI-powered emergency priority prediction
- **Intelligent QR Emergency System**: 
  - Scan Health ID QR cards to immediately fetch critically required patient stats.
  - Interactive In-App HTML5 Camera Scanner native to the User Dashboard.
  - Role-based privacy (Bystanders see only critical details like Blood Group & Emergency Contacts; Doctors see full medical history).
  - Customizable Emergency Contact mapping and universal quick-dial buttons (e.g. 112/108).
  - **Live Nearest Hospitals Locator**: Automatically tracks the user's GPS location via the browser and finds the closest ABHA-connected hospitals natively via a Haversine distance backend API, with one-tap fallbacks for Google Maps navigation.
- **ML Models**: 
  - SVM Health Risk Prediction Model
  - Logistic Regression Emergency Priority Model
- **OTP Verification**: Firebase-based OTP system
- **QR Code Generation**: Health ID QR codes

## Database

- **Type**: SQLite
- **Location**: `backend/health_system.db`
- **Tables**: users, doctors, hospitals, records, emergencies, otp_codes

## Configuration

- Templates: `frontend/templates/`
- Static files: `frontend/static/`
- Database: `backend/health_system.db`
- Models: `backend/pkl/`
- Uploads: `backend/uploads/`

## Deployment

The project is ready for deployment to various platforms:

- **Docker**: Use `Dockerfile` and `docker-compose.yml`
- **Heroku**: Use `Procfile` and `runtime.txt`
- **AWS/GCP/Azure**: Use `wsgi.py` with Gunicorn
- **Traditional VPS**: Use Nginx + Gunicorn (see `nginx.conf.example`)

See [DEPLOYMENT.md](DEPLOYMENT.md) for comprehensive deployment guides.

## Configuration

- **Environment Variables**: Copy `env.example` to `.env` and configure
- **Firebase Setup**: See `backend/FIREBASE_SETUP.md`
- **Production Config**: See `backend/config.py` and `DEPLOYMENT.md`

## Project Structure

The project has been organized with:
- **Backend**: All Python code, database, ML models, and server-side logic
- **Frontend**: All HTML templates, CSS, JavaScript, and static assets
- **Root**: Configuration files, deployment scripts, and documentation
