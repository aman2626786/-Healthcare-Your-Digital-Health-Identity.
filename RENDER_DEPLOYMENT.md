# Render.com Deployment Guide

Complete guide for deploying Swasthya Sampark on Render.com.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Deploy](#quick-deploy)
3. [Manual Setup](#manual-setup)
4. [Environment Variables](#environment-variables)
5. [Database Setup](#database-setup)
6. [Firebase Configuration](#firebase-configuration)
7. [File Storage](#file-storage)
8. [Troubleshooting](#troubleshooting)

## Prerequisites

- Render.com account (sign up at https://render.com)
- GitHub repository with your code (or GitLab/Bitbucket)
- Firebase account (for OTP verification)
- Python 3.11+ knowledge

## Quick Deploy

### Option 1: One-Click Deploy (Recommended)

1. **Fork/Clone Repository**
   - Push your code to GitHub/GitLab/Bitbucket

2. **Connect to Render**
   - Go to https://dashboard.render.com
   - Click "New +" → "Web Service"
   - Connect your repository

3. **Configure Service**
   - **Name**: `swasthya-sampark` (or your preferred name)
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn --config gunicorn_config.py wsgi:application`

4. **Set Environment Variables**
   - Go to Environment tab
   - Add all variables from `render.env` file
   - **IMPORTANT**: Generate a new `SECRET_KEY` (see below)

5. **Deploy**
   - Click "Create Web Service"
   - Wait for build and deployment

## Manual Setup

### Step 1: Create Web Service

1. Log in to Render Dashboard
2. Click "New +" → "Web Service"
3. Connect your Git repository
4. Select the repository and branch

### Step 2: Configure Build Settings

**Build Settings:**
```
Build Command: pip install -r requirements.txt
Start Command: gunicorn --config gunicorn_config.py wsgi:application
```

**Advanced Settings:**
- **Python Version**: 3.11 (or latest)
- **Root Directory**: `/` (project root)
- **Auto-Deploy**: Yes (recommended)

### Step 3: Set Environment Variables

Go to **Environment** tab and add these variables:

#### Required Variables

| Variable | Value | Description |
|----------|-------|-------------|
| `FLASK_APP` | `backend/app.py` | Flask application entry point |
| `FLASK_ENV` | `production` | Production environment |
| `FLASK_DEBUG` | `0` | Disable debug mode |
| `SECRET_KEY` | `[Generate below]` | Flask secret key (REQUIRED) |
| `FIREBASE_WEB_API_KEY` | `[Your API Key]` | Firebase Web API Key |

#### Optional Variables

| Variable | Value | Description |
|----------|-------|-------------|
| `OTP_CODE_LENGTH` | `6` | OTP code length |
| `OTP_EXPIRY_MINUTES` | `10` | OTP expiration time |
| `MAX_UPLOAD_SIZE` | `16777216` | Max upload size (16MB) |
| `LOG_LEVEL` | `INFO` | Logging level |
| `PRODUCTION` | `True` | Production flag |

### Step 4: Generate SECRET_KEY

**Option A: Using Python**
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

**Option B: Using OpenSSL**
```bash
openssl rand -hex 32
```

**Option C: Online Generator**
- Visit: https://randomkeygen.com/
- Use "CodeIgniter Encryption Keys" (256-bit)

Copy the generated key and paste it as `SECRET_KEY` value.

## Environment Variables

### Complete Environment Variable List

Copy these from `render.env` to Render dashboard:

```bash
FLASK_APP=backend/app.py
FLASK_ENV=production
FLASK_DEBUG=0
SECRET_KEY=your-generated-secret-key-here
FIREBASE_WEB_API_KEY=your-firebase-api-key-here
OTP_CODE_LENGTH=6
OTP_EXPIRY_MINUTES=10
MAX_UPLOAD_SIZE=16777216
PRODUCTION=True
LOG_LEVEL=INFO
```

### Setting Variables in Render

1. Go to your service in Render Dashboard
2. Click on **Environment** tab
3. Click **Add Environment Variable**
4. Enter **Key** and **Value**
5. Click **Save Changes**
6. Service will automatically redeploy

## Database Setup

### Option 1: SQLite (Default - Free)

SQLite works on Render, but with limitations:
- ✅ Data persists during service lifetime
- ✅ No additional cost
- ❌ Data lost if service is deleted
- ❌ Not suitable for high-traffic

**Configuration:**
- No additional setup needed
- Database file stored in service filesystem
- Works automatically with default `DATABASE_URL`

### Option 2: Render PostgreSQL (Recommended for Production)

1. **Create PostgreSQL Database**
   - Render Dashboard → "New +" → "PostgreSQL"
   - Choose plan (Free tier available)
   - Note the connection string

2. **Update Environment Variables**
   ```
   DATABASE_URL=postgresql://user:password@hostname:5432/dbname
   ```

3. **Update Application Code**
   - Install PostgreSQL adapter: Add `psycopg2-binary` to `requirements.txt`
   - Update `backend/app.py` to use PostgreSQL instead of SQLite

**Note**: Current version uses SQLite. PostgreSQL migration requires code changes.

## Firebase Configuration

### Step 1: Get Firebase Web API Key

1. Go to [Firebase Console](https://console.firebase.google.com)
2. Select your project (or create new)
3. Click ⚙️ **Project Settings**
4. Go to **General** tab
5. Scroll to **Your apps** section
6. Copy **Web API Key**

### Step 2: Set in Render

1. Go to Render Dashboard → Your Service → Environment
2. Add variable:
   - **Key**: `FIREBASE_WEB_API_KEY`
   - **Value**: Your copied API key
3. Save changes

### Step 3: Firebase Service Account (Optional)

For full Firebase Admin SDK features:

1. **Download Service Account JSON**
   - Firebase Console → Project Settings → Service Accounts
   - Click "Generate new private key"
   - Download JSON file

2. **Add to Render (Option A - Environment Variable)**
   - Convert JSON to single-line string
   - Add as `FIREBASE_CREDENTIALS_JSON` environment variable
   - Update code to parse JSON from environment variable

3. **Add to Render (Option B - Secret Files)**
   - Use Render's Secret Files feature
   - Upload JSON file
   - Reference path in environment variable

## File Storage

### Current Setup (Filesystem)

- Uploads stored in `backend/uploads/`
- QR codes stored in `frontend/static/qr/`
- **Limitation**: Files are ephemeral (lost on service restart/redeploy)

### Recommended: External Storage

For production, use external storage:

1. **AWS S3** (Recommended)
2. **Google Cloud Storage**
3. **Cloudinary** (for images)
4. **Render Disk** (Persistent storage - paid feature)

**Implementation**: Update file upload code to use external storage service.

## Build and Deploy

### Build Process

Render automatically:
1. Clones your repository
2. Runs `pip install -r requirements.txt`
3. Builds your application
4. Starts with `gunicorn --config gunicorn_config.py wsgi:application`

### Build Logs

Monitor build process:
- Go to **Logs** tab in Render Dashboard
- Watch for errors during build
- Check for missing dependencies

### Common Build Issues

**Issue**: `ModuleNotFoundError`
- **Solution**: Ensure all dependencies are in `requirements.txt`

**Issue**: `Port already in use`
- **Solution**: Render sets PORT automatically, don't override

**Issue**: `SECRET_KEY not set`
- **Solution**: Add `SECRET_KEY` environment variable

## Custom Domain

1. Go to **Settings** → **Custom Domains**
2. Click **Add Custom Domain**
3. Enter your domain
4. Follow DNS configuration instructions
5. SSL certificate is automatically provisioned

## Monitoring and Logs

### View Logs

- **Real-time**: Logs tab in Render Dashboard
- **Historical**: Logs are retained for 7 days (free) or longer (paid)

### Health Checks

- Render automatically monitors your service
- Health check endpoint: `/health` (if implemented)
- Service restarts automatically on failure

## Troubleshooting

### Service Won't Start

1. **Check Logs**
   - Go to Logs tab
   - Look for error messages
   - Common: Missing environment variables

2. **Check Environment Variables**
   - Ensure `SECRET_KEY` is set
   - Verify `FLASK_ENV=production`
   - Check `FIREBASE_WEB_API_KEY` is correct

3. **Check Build Logs**
   - Look for dependency installation errors
   - Verify Python version compatibility

### Database Errors

1. **SQLite Permission Issues**
   - Ensure database directory is writable
   - Check file permissions in logs

2. **Connection Errors**
   - Verify `DATABASE_URL` is correct
   - Check database service is running (if PostgreSQL)

### Firebase Not Working

1. **Check API Key**
   - Verify `FIREBASE_WEB_API_KEY` is set correctly
   - Ensure no extra spaces or quotes

2. **Check Service Account**
   - Verify JSON file is valid (if using)
   - Check file path is correct

### Static Files Not Loading

1. **Check Paths**
   - Verify `frontend/static/` exists in repository
   - Check Flask static folder configuration

2. **Check Build**
   - Ensure static files are included in build
   - Verify no `.gitignore` excludes them

### High Memory Usage

1. **Optimize Workers**
   - Edit `gunicorn_config.py`
   - Reduce `workers` count
   - Adjust `worker_connections`

2. **Upgrade Plan**
   - Render free tier: 512MB RAM
   - Consider upgrading for production

## Cost Optimization

### Free Tier Limits

- **512MB RAM**
- **0.1 CPU**
- **100GB bandwidth/month**
- **750 hours/month** (enough for 24/7)

### Paid Plans

- **Starter**: $7/month - 512MB RAM, better performance
- **Standard**: $25/month - 2GB RAM, better for production
- **Pro**: Custom pricing - More resources

## Security Checklist

- [ ] `SECRET_KEY` is strong and unique
- [ ] `FLASK_DEBUG=0` in production
- [ ] `FLASK_ENV=production`
- [ ] Firebase credentials are secure
- [ ] Environment variables are set (not hardcoded)
- [ ] Custom domain has SSL (automatic on Render)
- [ ] Database credentials are secure (if using PostgreSQL)

## Support

- **Render Docs**: https://render.com/docs
- **Render Support**: support@render.com
- **Community**: https://community.render.com

## Quick Reference

**Service URL Format:**
```
https://your-service-name.onrender.com
```

**Environment Variables Location:**
```
Dashboard → Your Service → Environment
```

**Logs Location:**
```
Dashboard → Your Service → Logs
```

**Redeploy:**
```
Dashboard → Your Service → Manual Deploy → Deploy latest commit
```

---

**Ready to Deploy?** Follow the [Quick Deploy](#quick-deploy) section above!

