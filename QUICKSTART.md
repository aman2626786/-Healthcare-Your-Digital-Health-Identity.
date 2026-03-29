# Quick Start Guide

Get Swasthya Sampark up and running in minutes!

## Prerequisites

- Python 3.11 or higher
- pip (Python package manager)

## Installation Steps

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment (Optional)

```bash
# Copy example environment file
cp env.example .env

# Edit .env with your settings (optional for development)
# For production, you MUST set SECRET_KEY and FIREBASE_WEB_API_KEY
```

### 3. Setup Firebase (Optional but Recommended)

**Option A: Using Web API Key (Simpler)**
1. Get your Firebase Web API Key from [Firebase Console](https://console.firebase.google.com)
2. Set it in `.env`:
   ```
   FIREBASE_WEB_API_KEY=your-api-key-here
   ```

**Option B: Using Service Account (Full Features)**
1. Download service account JSON from Firebase Console
2. Place it in `backend/pkl/firebase_service_account.json`

See `backend/FIREBASE_SETUP.md` for detailed instructions.

### 4. Run the Application

```bash
# Simple way
python run.py

# Or from backend directory
cd backend
python app.py
```

The application will be available at `http://localhost:5000`

## First Time Setup

1. **Register a User Account**
   - Go to `http://localhost:5000`
   - Click "Register" and create an account

2. **Register a Doctor Account**
   - Go to `http://localhost:5000/doctor/register`
   - Create a doctor account

3. **Register a Hospital Account**
   - Go to `http://localhost:5000/hospital/register`
   - Create a hospital account

## Development vs Production

### Development Mode (Default)
- Debug mode enabled
- Uses development secret key
- Detailed error messages
- Auto-reload on code changes

### Production Mode
1. Set environment variables:
   ```bash
   export FLASK_ENV=production
   export SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(32))')
   export FLASK_DEBUG=0
   ```

2. Use a production WSGI server:
   ```bash
   gunicorn --config gunicorn_config.py wsgi:application
   ```

## Using Docker (Alternative)

```bash
# Build image
docker build -t swasthya-sampark .

# Run container
docker-compose up -d
```

## Troubleshooting

### Import Errors
```bash
pip install -r requirements.txt
```

### Database Errors
The database is created automatically on first run. If you need to reset:
```bash
cd backend
rm health_system.db
python -c "from app import init_db; init_db()"
```

### Port Already in Use
Change the port in `.env`:
```
PORT=5001
```

### Firebase Not Working
- Check that `FIREBASE_WEB_API_KEY` is set correctly
- Or ensure service account JSON is in the correct location
- See `backend/FIREBASE_SETUP.md` for help

## Next Steps

- Read `DEPLOYMENT.md` for production deployment
- Check `backend/README.md` for backend details
- Review `backend/FIREBASE_SETUP.md` for Firebase configuration

## Need Help?

- Check the logs in the console
- Review `DEPLOYMENT.md` for detailed instructions
- Check individual component README files

