# 🚀 Quick Start Guide

## Server is Running! ✅

Your Django backend is now live at: **http://127.0.0.1:8000/**

## What You Have Now

✅ **Complete Authentication System**
- OTP-based email login with SMTP
- Session management
- User profiles

✅ **Insurance Management**
- Application creation and tracking
- Emirates ID OCR processing (mock)
- Product recommendations based on salary/location
- Policy creation with business rules
- One policy per Emirates ID enforcement

✅ **AI Chat System**
- Message storage
- Session-based conversations
- Chat history

## Next Steps

### 1. Create Admin User (Optional)

To access the Django admin panel:

```bash
python manage.py createsuperuser
```

Then visit: http://127.0.0.1:8000/admin/

### 2. Configure Email (For Production)

Edit `.env` file and add your Gmail credentials:

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

**For Gmail App Password:**
1. Go to https://myaccount.google.com/security
2. Enable 2-Step Verification
3. Go to App Passwords
4. Generate password for "Mail"
5. Use that password in `.env`

### 3. Test the Application

Open in browser: **http://127.0.0.1:8000/**

The frontend HTML is already integrated and ready to use!

### 4. API Testing

You can test the API endpoints using:

**Browser:** http://127.0.0.1:8000/api/auth/check/

**Curl:**
```bash
curl http://127.0.0.1:8000/api/auth/check/
```

**Postman/Insomnia:** Import the endpoints from README.md

## Available Endpoints

### Authentication
- `POST /api/auth/send-otp/` - Send OTP to email
- `POST /api/auth/verify-otp/` - Verify OTP and login
- `GET /api/auth/check/` - Check if user is authenticated
- `GET /api/auth/me/` - Get current user info
- `POST /api/auth/logout/` - Logout

### Insurance
- `GET /api/insurance/applications/` - List applications
- `POST /api/insurance/applications/` - Create application
- `POST /api/insurance/process-ocr/` - Upload Emirates ID
- `POST /api/insurance/recommendations/` - Get product recommendations
- `POST /api/insurance/create-policy/` - Create policy
- `GET /api/insurance/policies/` - List user policies
- `GET /api/insurance/policies/active/` - Get active policies
- `GET/POST /api/insurance/chat/` - Chat messages

## Current Configuration

📧 **Email Backend:** Console (prints to terminal)
- OTPs will be displayed in the terminal where server is running
- Perfect for development/testing
- Change to SMTP in `.env` for production

🗄️ **Database:** SQLite (db.sqlite3)
- Great for development
- Automatically created
- All data persists

🔒 **Security:** 
- Session-based authentication
- CSRF protection enabled
- CORS configured for localhost

## Development Tips

### 1. View Email OTPs
When you request an OTP, check the terminal where Django is running. You'll see:

```
Content-Type: text/plain; charset="utf-8"
MIME-Version: 1.0
Content-Transfer-Encoding: 7bit
Subject: Your Medical Insurance Portal OTP
From: webmaster@localhost
To: user@example.com
Date: ...

Your OTP for Medical Insurance Portal is: 1234

This OTP is valid for 10 minutes.
```

### 2. Access Admin Panel
After creating superuser:
1. Go to http://127.0.0.1:8000/admin/
2. View all OTPs, applications, policies
3. Manually manage data

### 3. Reset Database
If you want to start fresh:

```bash
# Stop server (Ctrl+C)
del db.sqlite3
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### 4. View API Response Format
All API responses follow this format:

**Success:**
```json
{
    "success": true,
    "message": "...",
    "data": {...}
}
```

**Error:**
```json
{
    "success": false,
    "message": "Error description"
}
```

## Testing Authentication Flow

### Test 1: Send OTP
```bash
curl -X POST http://127.0.0.1:8000/api/auth/send-otp/ \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'
```

Check terminal for OTP, then:

### Test 2: Verify OTP
```bash
curl -X POST http://127.0.0.1:8000/api/auth/verify-otp/ \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "otp_code": "1234"}' \
  -c cookies.txt
```

### Test 3: Check Auth
```bash
curl http://127.0.0.1:8000/api/auth/check/ \
  -b cookies.txt
```

## Common Issues & Solutions

### Issue: OTP not received
**Solution:** Check the terminal where server is running. In development mode, OTPs print there.

### Issue: CORS errors
**Solution:** Make sure you're accessing from http://127.0.0.1:8000, not localhost (they're treated differently).

### Issue: 403 Forbidden
**Solution:** Include `credentials: 'include'` in fetch requests for session cookies.

### Issue: Application won't start
**Solution:** 
```bash
python manage.py migrate
python manage.py runserver
```

## Production Deployment

Before deploying to production:

1. ✅ Set `DEBUG=False` in `.env`
2. ✅ Change `SECRET_KEY` to a strong random key
3. ✅ Configure real SMTP for emails
4. ✅ Use PostgreSQL instead of SQLite
5. ✅ Set up proper `ALLOWED_HOSTS`
6. ✅ Configure static file serving (WhiteNoise/S3)
7. ✅ Enable HTTPS
8. ✅ Add rate limiting for OTP requests

## Need Help?

📚 **Documentation:**
- README.md - Complete project documentation
- API_INTEGRATION_GUIDE.md - Frontend integration guide

📧 **Support:** Check the terminal logs for any errors

🐛 **Debugging:** 
- Django Admin: http://127.0.0.1:8000/admin/
- Server logs in terminal
- Check `db.sqlite3` with DB Browser for SQLite

---

## 🎉 You're All Set!

Your Medical Insurance backend is complete and running. The HTML frontend is already integrated and ready to use.

**Access the app:** http://127.0.0.1:8000/

**Test the login flow:**
1. Enter email
2. Get OTP from terminal
3. Enter OTP (or use "1234" for quick testing during development)
4. Start insurance application

Happy coding! 🚀
