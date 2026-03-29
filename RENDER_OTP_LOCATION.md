# Where to Find OTP on Render

## 📍 OTP Display Locations

When you request an OTP on Render, it appears in **3 places**:

### 1. ✅ **On the Login Page (Most Visible)**

**Location**: Right below the OTP input field

**What you'll see**:
```
┌─────────────────────────────────┐
│   📱 Your OTP Code:             │
│                                  │
│        1 2 3 4 5 6              │
│                                  │
│   Valid for 10 minutes           │
└─────────────────────────────────┘
```

**Steps to see it**:
1. Go to your Render URL: `https://your-app.onrender.com`
2. Click **Hospital Login** / **Doctor Login** / **User Login**
3. Select **"OTP Login"** radio button
4. Enter your **Email** and **Phone Number**
5. Click **"Send OTP"**
6. **The OTP code will appear in a large green box** below the phone input field

### 2. ✅ **Flash Message at Top of Page**

**Location**: At the very top of the page (below the header)

**What you'll see**:
- Green success message: `"OTP sent successfully. Your OTP code is: 123456 (expires in 10 minutes). Check Render logs if not visible."`

### 3. ✅ **Render Dashboard Logs**

**Location**: Render Dashboard → Your Service → Logs tab

**What you'll see**:
```
[OTP DEBUG] OTP for 1234567890 (hospital): 123456
[OTP INFO] OTP stored in database. Expires at: 2025-12-14T03:30:00
```

**Steps to view logs**:
1. Go to https://dashboard.render.com
2. Click on your service
3. Click **"Logs"** tab (left sidebar)
4. Look for lines starting with `[OTP DEBUG]`
5. The 6-digit number after the colon is your OTP

## 🎯 Quick Guide: Getting Your OTP

### Method 1: On the Page (Easiest)
1. Request OTP on login page
2. Look for the **large green box** with the OTP code
3. Copy the 6-digit number
4. Enter it in the OTP field

### Method 2: From Flash Message
1. Request OTP
2. Look at the **top of the page** for green success message
3. The OTP code is in the message text

### Method 3: From Render Logs (If page doesn't show)
1. Request OTP
2. Go to Render Dashboard → Logs
3. Find `[OTP DEBUG]` line
4. Copy the 6-digit code

## 📱 Visual Guide

### Login Page Layout:
```
┌─────────────────────────────────────┐
│  [Flash Message with OTP]          │  ← Top of page
├─────────────────────────────────────┤
│  Hospital Admin Login               │
│                                     │
│  [Password] [OTP Login] ◄─── Select this
│                                     │
│  Email: admin@hospital.com          │
│  Phone: 1234567890                  │
│  [Send OTP]                         │
│                                     │
│  ┌─────────────────────────────┐   │
│  │ 📱 Your OTP Code:           │   │  ← HERE!
│  │                             │   │
│  │     1 2 3 4 5 6            │   │
│  │                             │   │
│  │ Valid for 10 minutes        │   │
│  └─────────────────────────────┘   │
│                                     │
│  [Enter OTP field appears here]     │
│  [Verify OTP]                       │
└─────────────────────────────────────┘
```

## 🔍 Troubleshooting

### OTP Not Showing on Page?

1. **Check if OTP was sent**:
   - Look for flash message at top
   - Check Render logs for `[OTP DEBUG]`

2. **Check browser console**:
   - Press F12 → Console tab
   - Look for JavaScript errors

3. **Verify template rendering**:
   - Make sure `otp_sent=True` is passed to template
   - Check that green box HTML is in template

4. **Check Render logs**:
   - Go to Dashboard → Logs
   - Look for errors or warnings

### OTP Code Not Visible?

**If the green box doesn't appear**, the OTP is still available in:
- ✅ Flash message at top of page
- ✅ Render Dashboard logs
- ✅ Database (if you have access)

## 💡 Pro Tip

**For Testing**: The OTP is always logged in Render logs, so you can:
1. Request OTP
2. Immediately check Render logs
3. Copy the OTP code
4. Use it to login

This works even if the page display has issues!

## 📝 Example OTP Request Flow

1. **User Action**: 
   - Goes to `/hospital/login`
   - Selects "OTP Login"
   - Enters email: `admin@hospital.com`
   - Enters phone: `1234567890`
   - Clicks "Send OTP"

2. **Backend Response**:
   - Generates OTP: `456789`
   - Stores in database
   - Logs: `[OTP DEBUG] OTP for 1234567890 (hospital): 456789`
   - Returns template with `otp_code=456789`

3. **Page Display**:
   - Flash message shows: "OTP sent successfully. Your OTP code is: 456789..."
   - Green box shows: Large "456789" in center
   - User enters `456789` in OTP field
   - Clicks "Verify OTP"
   - ✅ Login successful!

---

**Remember**: The OTP is **always** visible in at least one of these locations. If you can't see it on the page, check the Render logs!

