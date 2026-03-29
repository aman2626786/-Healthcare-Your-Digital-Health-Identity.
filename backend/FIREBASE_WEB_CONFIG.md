# Firebase Web Configuration Guide

## Overview
This application supports Firebase Web API Key configuration for client-side operations and Firebase Admin SDK for server-side operations.

## Configuration Methods

### Method 1: Service Account JSON (Recommended for Admin SDK)
- File: `firebase_service_account.json`
- Location: `vgu/firebase_service_account.json`
- Use: Full Admin SDK features

### Method 2: Web API Key (For Client-Side)
- Environment Variable: `FIREBASE_WEB_API_KEY`
- Or: Set in code (already configured)
- Use: Client-side Firebase operations

## Current Configuration

Your Firebase Web API Key is configured:
```
BC5Hbsevk0B2jrRVwGVm0iMK0mq-2DaefIRLd_0aueAUz6LABC5jApBBqkfvLw6vTB3PWAwsCgsdkvvC2QlMa_c
```

## Setup Instructions

### Option A: Using Service Account (Full Features)

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select your project
3. Go to **Project Settings** → **Service Accounts**
4. Click **Generate New Private Key**
5. Save as `firebase_service_account.json` in the `vgu` directory

### Option B: Using Web API Key (Current Setup)

The web API key is already configured in the code. For production:

1. Set environment variable:
   ```bash
   export FIREBASE_WEB_API_KEY="your-api-key"
   ```

2. Or update in `app.py`:
   ```python
   FIREBASE_WEB_API_KEY = "your-api-key"
   ```

## Features Available

### With Service Account JSON:
- ✅ Full Firebase Admin SDK features
- ✅ Server-side user management
- ✅ Custom token generation
- ✅ Phone number verification
- ✅ Database operations

### With Web API Key Only:
- ✅ Client-side Firebase operations
- ✅ Phone number format validation
- ✅ Basic Firebase features
- ⚠️ Limited Admin SDK features

## Integration Status

- **Firebase Admin SDK**: Installed ✅
- **Web API Key**: Configured ✅
- **Service Account**: Optional (for full features)

## Next Steps

1. **For Development**: Current setup works with database storage
2. **For Production**: 
   - Add service account JSON for full Admin SDK features
   - Or integrate Firebase Cloud Functions for SMS sending
   - Or use third-party SMS service (Twilio, AWS SNS, etc.)

## Security

- Web API Key is safe to expose in client-side code
- Service Account JSON must be kept secret
- Never commit service account JSON to version control

