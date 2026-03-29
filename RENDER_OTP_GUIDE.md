# How to Get OTP on Render

## Current Implementation

The OTP system generates and stores OTP codes in the database, but **does not send SMS messages**. This is because SMS sending requires additional service integration (Firebase Cloud Functions, Twilio, etc.).

## How to Get Your OTP Code

### Method 1: Check Render Logs (Recommended)

1. Go to your Render Dashboard
2. Select your service
3. Click on **Logs** tab
4. Look for lines that say:
   ```
   [OTP DEBUG] OTP for 1234567890 (user): 123456
   ```
5. The OTP code is the 6-digit number after the colon

### Method 2: Check Application Response

When you request an OTP, the response message will include the OTP code:
- **Development**: OTP is shown directly in the success message
- **Production**: OTP is included in the message (for now, until SMS is integrated)

### Method 3: Database Query (Advanced)

You can query the database directly:
```sql
SELECT code, phone, role, expires_at 
FROM otp_codes 
WHERE phone = 'YOUR_PHONE' 
  AND verified = 0 
  AND expires_at > datetime('now')
ORDER BY created_at DESC 
LIMIT 1;
```

## Current Behavior

✅ **What Works:**
- OTP generation (6 digits)
- OTP storage in database
- OTP verification
- OTP expiration (10 minutes)
- OTP visible in Render logs

❌ **What Doesn't Work:**
- Actual SMS sending (requires SMS service integration)
- OTP delivery via phone

## Integration Options for SMS

### Option 1: Firebase Phone Authentication
- Use Firebase Auth's built-in phone verification
- Handles SMS sending automatically
- Requires Firebase project setup

### Option 2: Twilio
- Popular SMS service
- Requires Twilio account and API keys
- Add to `requirements.txt`: `twilio`
- Cost: ~$0.0075 per SMS

### Option 3: AWS SNS
- Amazon's SMS service
- Requires AWS account
- Cost: ~$0.00645 per SMS

### Option 4: Firebase Cloud Functions
- Custom SMS sending via Firebase
- Requires Firebase Functions setup
- Can use Twilio or other services

## Quick Fix: Show OTP in Response

The current code has been updated to show OTP in the response message. When you request OTP:

1. You'll see: "OTP sent successfully. Your OTP is: 123456"
2. Or check Render logs for: `[OTP DEBUG] OTP for...`

## Testing OTP on Render

1. **Request OTP**: Enter your email/Health ID and phone number
2. **Check Logs**: Go to Render Dashboard → Logs
3. **Find OTP**: Look for `[OTP DEBUG]` line
4. **Enter OTP**: Use the 6-digit code to login/reset password

## Future Enhancement

To enable actual SMS sending, you need to:

1. **Choose SMS Service** (Twilio recommended)
2. **Add API Keys** to Render environment variables
3. **Update `send_otp()` function** to call SMS API
4. **Test** with real phone numbers

## Example: Twilio Integration

```python
from twilio.rest import Client

def send_otp_sms(phone, otp_code):
    account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
    auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
    from_number = os.environ.get('TWILIO_PHONE_NUMBER')
    
    client = Client(account_sid, auth_token)
    message = client.messages.create(
        body=f'Your OTP code is: {otp_code}',
        from_=from_number,
        to=f'+{phone}'
    )
    return message.sid
```

Then add to `send_otp()`:
```python
# Send SMS via Twilio
send_otp_sms(phone, otp_code)
```

## Environment Variables Needed (for SMS)

If you want to add SMS sending, add these to Render:

```
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+1234567890
```

Or for Firebase:
```
FIREBASE_WEB_API_KEY=your_api_key
FIREBASE_PROJECT_ID=your_project_id
```

---

**For now**: Check Render logs to get your OTP code when testing!

