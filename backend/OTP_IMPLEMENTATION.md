# OTP Implementation for Password Reset and Login

## Overview
Implemented OTP (One-Time Password) functionality for password reset and login using the OTP.dev API.

## Features Implemented

### 1. OTP Login
- Users can login using OTP instead of password
- Available for all three roles: User (Patient), Doctor, Hospital Admin
- OTP is sent via SMS using the OTP.dev API
- OTP expires after 10 minutes

### 2. Forgot Password
- Password reset via OTP verification
- Two-step process:
  1. Request OTP (enter email/Health ID + phone)
  2. Verify OTP and set new password

## API Configuration

The OTP API is configured in `app.py`:
```python
OTP_API_KEY = 'f2cbc22d60bf0c2ac5f49574ac0b6639'
OTP_API_URL = 'https://api.otp.dev/v1/verifications'
OTP_SENDER_ID = '80807153-76e4-4c7b-9ef5-de02166b6be3'
OTP_TEMPLATE_ID = 'ae84188b-8ccb-4324-aaab-131aebdb4600'
OTP_CODE_LENGTH = 6
OTP_EXPIRY_MINUTES = 10
```

## Database Changes

### New Table: `otp_codes`
Stores OTP codes for verification:
- `phone`: Phone number
- `code`: OTP code
- `role`: User role (user/doctor/hospital)
- `identifier`: Email or Health ID
- `purpose`: 'login' or 'reset'
- `created_at`: Timestamp
- `expires_at`: Expiration timestamp
- `verified`: Whether OTP has been used

### Updated Tables
- `doctors`: Added `phone` column
- `hospitals`: Added `phone` column
- `users`: Already had `phone` column

## Routes Added

### Login Routes (Updated)
- `/user/login` - Now supports OTP login
- `/doctor/login` - Now supports OTP login
- `/hospital/login` - Now supports OTP login

### Forgot Password Routes (New)
- `/user/forgot_password` - Password reset for patients
- `/doctor/forgot_password` - Password reset for doctors
- `/hospital/forgot_password` - Password reset for hospitals

## Templates Updated

1. **user_login.html**
   - Toggle between Password and OTP login
   - Forgot Password link
   - OTP input field when OTP mode is selected

2. **doctor_login.html**
   - Toggle between Password and OTP login
   - Forgot Password link
   - OTP input field when OTP mode is selected

3. **hospital_login.html**
   - Toggle between Password and OTP login
   - Forgot Password link
   - OTP input field when OTP mode is selected

4. **forgot_password.html** (New)
   - Two-step form for password reset
   - Step 1: Request OTP
   - Step 2: Verify OTP and set new password

## How It Works

### OTP Login Flow
1. User selects "OTP Login" option
2. Enters Health ID/Email + Phone number
3. Clicks "Send OTP"
4. System sends OTP via SMS API
5. User enters OTP code
6. System verifies OTP and logs in user

### Forgot Password Flow
1. User clicks "Forgot Password" link
2. Enters Health ID/Email + Phone number
3. System sends OTP via SMS
4. User enters OTP + New Password + Confirm Password
5. System verifies OTP and updates password
6. User redirected to login page

## Security Features

1. **OTP Expiration**: OTPs expire after 10 minutes
2. **Single Use**: Each OTP can only be used once
3. **Phone Verification**: Phone number must match the account
4. **Role-based**: OTPs are tied to specific roles and identifiers

## Dependencies

- `requests` library for API calls
- Install with: `pip install requests`

## Testing

### Development Mode
- OTP codes are printed to console for testing
- Format: `[OTP DEBUG] OTP for {phone} ({role}): {code}`

### Production
- Remove debug print statements
- Ensure phone numbers are properly formatted (with country code)
- Test with actual SMS delivery

## Notes

1. **Phone Number Format**: Ensure phone numbers include country code (e.g., 916377429064)
2. **API Response**: The OTP.dev API generates and sends the OTP. The current implementation stores a generated OTP for verification. If the API provides a verification endpoint, consider using it instead.
3. **Error Handling**: All API errors are caught and displayed to users
4. **Database Migration**: Phone columns are added automatically if they don't exist

## Future Enhancements

1. Use OTP.dev verification endpoint for OTP validation
2. Add rate limiting for OTP requests
3. Add OTP resend functionality
4. Add OTP expiration countdown timer in UI
5. Add phone number validation

