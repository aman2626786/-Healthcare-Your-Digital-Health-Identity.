# Fix: SECRET_KEY Error on Render

## Problem
```
ValueError: SECRET_KEY environment variable must be set in production
```

## Solution

The error occurs because `SECRET_KEY` environment variable is not set in Render.

### Quick Fix (2 Steps)

**Step 1: Generate a SECRET_KEY**

Run this command locally:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Or use online: https://randomkeygen.com/ (use "CodeIgniter Encryption Keys")

**Step 2: Add to Render**

1. Go to Render Dashboard
2. Select your service
3. Click **Environment** tab
4. Click **Add Environment Variable**
5. Set:
   - **Key**: `SECRET_KEY`
   - **Value**: [Paste the generated key]
6. Click **Save Changes**
7. Service will automatically redeploy

## Example SECRET_KEY

A valid SECRET_KEY looks like:
```
a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6
```

Or:
```
f47ac10b-58cc-4372-a567-0e02b2c3d479
```

## Verification

After adding SECRET_KEY:
1. Check deployment logs
2. Service should start successfully
3. Visit your service URL to verify

## Additional Required Variables

Make sure these are also set in Render:

- `FLASK_APP=backend/app.py`
- `FLASK_ENV=production`
- `FLASK_DEBUG=0`
- `FIREBASE_WEB_API_KEY=[Your Firebase Key]`

See `render.env` for complete list.

