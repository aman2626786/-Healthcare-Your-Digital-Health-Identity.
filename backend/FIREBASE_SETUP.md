# Firebase Admin SDK Setup Guide

## Overview
This application uses Firebase Admin SDK for OTP verification. Follow these steps to set up Firebase.

## Prerequisites
1. A Firebase project (create at https://console.firebase.google.com/)
2. Firebase Admin SDK service account key

## Installation

### 1. Install Firebase Admin SDK
```bash
pip install firebase-admin
```

### 2. Get Firebase Service Account Key

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select your project (or create a new one)
3. Go to **Project Settings** (gear icon)
4. Navigate to **Service Accounts** tab
5. Click **Generate New Private Key**
6. Download the JSON file
7. Save it as `firebase_service_account.json` in the `vgu` directory

### 3. File Structure
```
vgu/
├── app.py
├── firebase_service_account.json  ← Place your Firebase credentials here (NOT in git)
├── firebase_service_account.json.example  ← Example template (safe to commit)
├── .gitignore  ← Ensures credentials are not committed
├── ...
```

**Important:** 
- Copy `firebase_service_account.json.example` to `firebase_service_account.json`
- Fill in your actual Firebase credentials
- The `.gitignore` file ensures credentials are never committed to version control

## Firebase Configuration

The application will automatically:
- Initialize Firebase Admin SDK on startup
- Use Firebase for phone number validation
- Store OTP codes in the database
- Verify OTP codes using Firebase Admin SDK

## Phone Number Format

Firebase requires phone numbers in E.164 format:
- Format: `+[country code][number]`
- Example: `+916377429064` (India)
- Example: `+1234567890` (USA)

The application automatically normalizes phone numbers, but ensure your database stores them in the correct format.

## SMS Integration

**Note:** Firebase Admin SDK doesn't directly send SMS. For production:

1. **Option 1: Use Firebase Authentication**
   - Implement Firebase Auth on the frontend
   - Use Firebase Admin SDK for server-side verification
   - Firebase handles SMS sending automatically

2. **Option 2: Use Firebase Cloud Functions**
   - Create a Cloud Function to send SMS
   - Integrate with Twilio, AWS SNS, or similar service
   - Call the function from your Flask app

3. **Option 3: Use Third-party SMS Service**
   - Keep current database-based OTP storage
   - Integrate SMS sending service (Twilio, AWS SNS, etc.)
   - Use Firebase Admin SDK for additional verification

## Current Implementation

The current implementation:
- Generates OTP codes
- Stores them in the database
- Verifies OTP codes using database lookup
- Uses Firebase Admin SDK for phone number validation (if configured)

## Troubleshooting

### Error: "Firebase credentials file not found"
- Ensure `firebase_service_account.json` exists in the `vgu` directory
- Check file permissions

### Error: "Failed to initialize Firebase Admin SDK"
- Verify the JSON file is valid
- Check that the service account has proper permissions
- Ensure `firebase-admin` package is installed

### OTP not sending
- Current implementation stores OTP but doesn't send SMS
- Integrate SMS service or Firebase Cloud Functions
- For development, check console for OTP code

## Security Notes

1. **Never commit `firebase_service_account.json` to version control**
2. Add to `.gitignore`:
   ```
   firebase_service_account.json
   ```
3. Use environment variables for production
4. Restrict service account permissions in Firebase Console

## Next Steps

1. Set up Firebase project
2. Download service account key
3. Place file in `vgu` directory
4. Install `firebase-admin` package
5. Restart the application
6. (Optional) Integrate SMS sending service

