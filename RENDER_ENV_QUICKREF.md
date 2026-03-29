# Render.com Environment Variables - Quick Reference

Copy and paste these into Render Dashboard → Your Service → Environment

## 🔴 REQUIRED Variables (Must Set)

```bash
FLASK_APP=backend/app.py
FLASK_ENV=production
FLASK_DEBUG=0
SECRET_KEY=PASTE-YOUR-GENERATED-SECRET-KEY-HERE
FIREBASE_WEB_API_KEY=PASTE-YOUR-FIREBASE-API-KEY-HERE
```

## 🟡 Recommended Variables

```bash
OTP_CODE_LENGTH=6
OTP_EXPIRY_MINUTES=10
MAX_UPLOAD_SIZE=16777216
PRODUCTION=True
LOG_LEVEL=INFO
```

## 📝 How to Set in Render

1. Go to https://dashboard.render.com
2. Select your service
3. Click **Environment** tab (left sidebar)
4. Click **Add Environment Variable**
5. Enter **Key** and **Value**
6. Click **Save Changes**
7. Service will auto-redeploy

## 🔑 Generate SECRET_KEY

**Option 1: Python**
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

**Option 2: Online**
Visit: https://randomkeygen.com/
Use: "CodeIgniter Encryption Keys" (256-bit)

**Option 3: OpenSSL**
```bash
openssl rand -hex 32
```

## 🔥 Get Firebase API Key

1. Go to https://console.firebase.google.com
2. Select your project
3. ⚙️ **Project Settings** → **General** tab
4. Scroll to **Your apps** → **Web API Key**
5. Copy and paste as `FIREBASE_WEB_API_KEY`

## ✅ Complete Environment Variables List

Copy this entire block and fill in the values:

```
FLASK_APP=backend/app.py
FLASK_ENV=production
FLASK_DEBUG=0
SECRET_KEY=CHANGE-THIS-TO-A-STRONG-RANDOM-SECRET-KEY-MINIMUM-32-CHARACTERS
FIREBASE_WEB_API_KEY=your-firebase-web-api-key-here
OTP_CODE_LENGTH=6
OTP_EXPIRY_MINUTES=10
MAX_UPLOAD_SIZE=16777216
PRODUCTION=True
LOG_LEVEL=INFO
```

## 🚀 Render Build & Start Commands

**Build Command:**
```
pip install -r requirements.txt
```

**Start Command:**
```
gunicorn --config gunicorn_config.py wsgi:application
```

## ⚠️ Important Notes

- **SECRET_KEY**: Must be at least 32 characters, use a strong random value
- **FIREBASE_WEB_API_KEY**: Required for OTP login to work
- **PORT**: Render sets this automatically, don't override
- **HOST**: Render sets this automatically, don't override
- All values are case-sensitive
- No quotes needed around values
- Service redeploys automatically after saving environment variables

## 📚 Full Documentation

See `RENDER_DEPLOYMENT.md` for complete deployment guide.

