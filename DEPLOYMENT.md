# Deployment Guide

This guide covers deploying Swasthya Sampark to various platforms.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development Setup](#local-development-setup)
3. [Production Deployment](#production-deployment)
4. [Docker Deployment](#docker-deployment)
5. [Platform-Specific Guides](#platform-specific-guides)
6. [Environment Variables](#environment-variables)
7. [Database Setup](#database-setup)
8. [Firebase Configuration](#firebase-configuration)
9. [Troubleshooting](#troubleshooting)

## Prerequisites

- Python 3.11 or higher
- pip (Python package manager)
- Git (for version control)
- Firebase account (for OTP verification)
- Domain name and SSL certificate (for production)

## Local Development Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd vgu
```

### 2. Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and set your configuration
# - SECRET_KEY: Generate a secure random key
# - FIREBASE_WEB_API_KEY: Your Firebase Web API Key
```

### 5. Setup Firebase

1. Download Firebase service account JSON file
2. Place it in `backend/pkl/firebase_service_account.json`
3. Or set `FIREBASE_WEB_API_KEY` in `.env`

See `backend/FIREBASE_SETUP.md` for detailed instructions.

### 6. Initialize Database

The database will be automatically created on first run. To manually initialize:

```bash
cd backend
python -c "from app import init_db; init_db()"
```

### 7. Run the Application

```bash
# From project root
python run.py

# Or from backend directory
cd backend
python app.py
```

The application will be available at `http://localhost:5000`

## Production Deployment

### Using Gunicorn (Recommended)

1. **Install Gunicorn** (already in requirements.txt)

2. **Run with Gunicorn**:

```bash
gunicorn --config gunicorn_config.py wsgi:application
```

3. **With custom settings**:

```bash
gunicorn --bind 0.0.0.0:5000 --workers 4 --timeout 30 wsgi:application
```

### Using uWSGI (Alternative)

1. **Install uWSGI**:

```bash
pip install uwsgi
```

2. **Create uwsgi.ini**:

```ini
[uwsgi]
module = wsgi:application
master = true
processes = 4
socket = 0.0.0.0:5000
chmod-socket = 666
vacuum = true
die-on-term = true
```

3. **Run**:

```bash
uwsgi --ini uwsgi.ini
```

### Behind Nginx Reverse Proxy

1. **Install Nginx**:

```bash
# Ubuntu/Debian
sudo apt-get install nginx

# CentOS/RHEL
sudo yum install nginx
```

2. **Create Nginx Configuration** (`/etc/nginx/sites-available/swasthya-sampark`):

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Static files
    location /static {
        alias /path/to/vgu/frontend/static;
        expires 30d;
    }

    # Uploads
    location /uploads {
        alias /path/to/vgu/backend/uploads;
    }
}
```

3. **Enable Site**:

```bash
sudo ln -s /etc/nginx/sites-available/swasthya-sampark /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

4. **Setup SSL with Let's Encrypt**:

```bash
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

## Docker Deployment

### Build and Run

```bash
# Build the image
docker build -t swasthya-sampark .

# Run the container
docker run -d \
  --name swasthya-sampark \
  -p 5000:5000 \
  -e SECRET_KEY=your-secret-key \
  -e FIREBASE_WEB_API_KEY=your-api-key \
  -v $(pwd)/backend/health_system.db:/app/backend/health_system.db \
  -v $(pwd)/backend/uploads:/app/backend/uploads \
  -v $(pwd)/frontend/static/qr:/app/frontend/static/qr \
  swasthya-sampark
```

### Using Docker Compose

```bash
# Create .env file
cp .env.example .env
# Edit .env with your values

# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Platform-Specific Guides

### Heroku

1. **Install Heroku CLI** and login:

```bash
heroku login
```

2. **Create Heroku App**:

```bash
heroku create swasthya-sampark
```

3. **Set Environment Variables**:

```bash
heroku config:set SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(32))')
heroku config:set FIREBASE_WEB_API_KEY=your-api-key
heroku config:set FLASK_ENV=production
```

4. **Deploy**:

```bash
git push heroku main
```

5. **Run Database Migrations**:

```bash
heroku run python -c "from backend.app import init_db; init_db()"
```

### Railway

1. **Connect Repository** to Railway
2. **Set Environment Variables** in Railway dashboard
3. **Deploy** - Railway auto-detects and deploys

### Render.com

**Quick Deploy:**

1. **Connect Repository**
   - Go to https://dashboard.render.com
   - Click "New +" → "Web Service"
   - Connect your Git repository

2. **Configure Service**
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn --config gunicorn_config.py wsgi:application`
   - **Environment**: Python 3

3. **Set Environment Variables** (see `render.env` or `RENDER_ENV_QUICKREF.md`)
   - `FLASK_APP=backend/app.py`
   - `FLASK_ENV=production`
   - `FLASK_DEBUG=0`
   - `SECRET_KEY=[Generate with: python -c "import secrets; print(secrets.token_hex(32))"]`
   - `FIREBASE_WEB_API_KEY=[Your Firebase API Key]`

4. **Deploy**
   - Click "Create Web Service"
   - Service will build and deploy automatically

**For detailed Render deployment guide, see `RENDER_DEPLOYMENT.md`**

### AWS Elastic Beanstalk

1. **Install EB CLI**:

```bash
pip install awsebcli
```

2. **Initialize EB**:

```bash
eb init -p python-3.11 swasthya-sampark
```

3. **Create Environment**:

```bash
eb create swasthya-sampark-env
```

4. **Set Environment Variables**:

```bash
eb setenv SECRET_KEY=your-secret-key FIREBASE_WEB_API_KEY=your-api-key
```

5. **Deploy**:

```bash
eb deploy
```

### DigitalOcean App Platform

1. **Create App** from GitHub repository
2. **Configure Build Command**: `pip install -r requirements.txt`
3. **Configure Run Command**: `gunicorn --config gunicorn_config.py wsgi:application`
4. **Set Environment Variables** in dashboard
5. **Deploy**

### Google Cloud Run

1. **Build and Push Image**:

```bash
gcloud builds submit --tag gcr.io/PROJECT-ID/swasthya-sampark
```

2. **Deploy**:

```bash
gcloud run deploy swasthya-sampark \
  --image gcr.io/PROJECT-ID/swasthya-sampark \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

## Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `SECRET_KEY` | Flask secret key for sessions | Yes (Production) | `dev-secret-key-change-in-prod` |
| `FLASK_ENV` | Flask environment | No | `development` |
| `FLASK_DEBUG` | Enable debug mode | No | `0` |
| `HOST` | Server host | No | `0.0.0.0` |
| `PORT` | Server port | No | `5000` |
| `FIREBASE_WEB_API_KEY` | Firebase Web API Key | Recommended | - |
| `FIREBASE_CREDENTIALS_PATH` | Path to Firebase service account JSON | Optional | `backend/pkl/...` |
| `OTP_CODE_LENGTH` | OTP code length | No | `6` |
| `OTP_EXPIRY_MINUTES` | OTP expiration time | No | `10` |
| `MAX_UPLOAD_SIZE` | Max file upload size (bytes) | No | `16777216` (16MB) |
| `LOG_LEVEL` | Logging level | No | `INFO` |

## Database Setup

### SQLite (Default)

The application uses SQLite by default. The database is automatically created at `backend/health_system.db`.

**For Production**: Consider migrating to PostgreSQL or MySQL for better performance and reliability.

### PostgreSQL Migration

1. **Install PostgreSQL adapter**:

```bash
pip install psycopg2-binary
```

2. **Update `config.py`**:

```python
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://user:pass@localhost/dbname')
```

3. **Update `app.py`** to use SQLAlchemy or psycopg2 instead of sqlite3.

## Firebase Configuration

See `backend/FIREBASE_SETUP.md` for detailed Firebase setup instructions.

**Quick Setup**:

1. Create Firebase project at https://console.firebase.google.com
2. Enable Authentication → Phone provider
3. Get Web API Key from Project Settings → General
4. Download Service Account Key from Project Settings → Service Accounts
5. Set `FIREBASE_WEB_API_KEY` in environment variables
6. Place service account JSON in `backend/pkl/` or set `FIREBASE_CREDENTIALS_PATH`

## Troubleshooting

### Application Won't Start

- **Check Python version**: `python --version` (should be 3.11+)
- **Check dependencies**: `pip install -r requirements.txt`
- **Check environment variables**: Ensure `.env` is configured
- **Check logs**: Look for error messages in console

### Database Errors

- **Permission issues**: Ensure database file is writable
- **Migration needed**: Run `init_db()` to update schema
- **Lock errors**: Ensure only one instance accesses SQLite at a time

### Firebase OTP Not Working

- **Check API key**: Verify `FIREBASE_WEB_API_KEY` is set correctly
- **Check service account**: Ensure JSON file is valid and in correct location
- **Check phone format**: Phone numbers should be in E.164 format (+91...)
- **See logs**: Check console for Firebase initialization messages

### Static Files Not Loading

- **Check paths**: Ensure `frontend/static/` exists
- **Check Nginx config**: If using reverse proxy, verify static file serving
- **Check permissions**: Ensure files are readable

### Model Loading Errors

- **Check model files**: Ensure `.pkl` files exist in `backend/pkl/`
- **Check dependencies**: Ensure `scikit-learn`, `numpy`, `joblib` are installed
- **Version compatibility**: Models trained with scikit-learn 1.3.2

### Port Already in Use

```bash
# Find process using port 5000
# Windows
netstat -ano | findstr :5000

# Linux/Mac
lsof -i :5000

# Kill process or change PORT in .env
```

## Security Checklist

- [ ] Change `SECRET_KEY` to a strong random value
- [ ] Set `FLASK_ENV=production` and `FLASK_DEBUG=0`
- [ ] Use HTTPS (SSL/TLS certificate)
- [ ] Set secure session cookies (`SESSION_COOKIE_SECURE=True`)
- [ ] Restrict file uploads (size, type validation)
- [ ] Use environment variables for sensitive data
- [ ] Don't commit `.env` or Firebase credentials
- [ ] Regularly update dependencies
- [ ] Use a production WSGI server (Gunicorn, uWSGI)
- [ ] Set up proper firewall rules
- [ ] Enable database backups
- [ ] Monitor logs for suspicious activity

## Support

For issues and questions:
- Check logs: `docker-compose logs` or application console
- Review documentation: `backend/README.md`, `backend/FIREBASE_SETUP.md`
- Check GitHub issues (if applicable)

