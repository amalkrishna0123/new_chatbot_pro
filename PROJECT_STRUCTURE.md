# 📊 Project Structure Overview

## Directory Tree

```
medical-insurance-backend/
│
├── 📁 medical_insurance/          # Django project settings
│   ├── __init__.py
│   ├── settings.py               # ✅ Configured with SMTP, CORS, REST
│   ├── urls.py                   # ✅ API routes configured
│   ├── asgi.py
│   └── wsgi.py
│
├── 📁 authentication/             # Authentication app
│   ├── migrations/
│   │   └── 0001_initial.py       # ✅ Database schema
│   ├── __init__.py
│   ├── admin.py                  # ✅ Admin panel config
│   ├── apps.py
│   ├── models.py                 # ✅ OTP, UserProfile
│   ├── serializers.py            # ✅ API serializers
│   ├── urls.py                   # ✅ Auth endpoints
│   ├── views.py                  # ✅ OTP send/verify, login/logout
│   └── tests.py
│
├── 📁 insurance/                  # Insurance app
│   ├── migrations/
│   │   └── 0001_initial.py       # ✅ Database schema
│   ├── __init__.py
│   ├── admin.py                  # ✅ Admin panel config
│   ├── apps.py
│   ├── models.py                 # ✅ Application, Policy, ChatMessage
│   ├── serializers.py            # ✅ API serializers
│   ├── urls.py                   # ✅ Insurance endpoints
│   ├── views.py                  # ✅ CRUD, OCR, recommendations
│   └── tests.py
│
├── 📁 templates/                  # HTML templates
│   └── index.html                # ✅ Your frontend UI
│
├── 📁 static/                     # Static files (CSS, JS, images)
│   └── (empty - using CDN)
│
├── 📁 media/                      # Uploaded files
│   └── emirates_ids/             # Emirates ID documents
│
├── 📄 manage.py                   # Django management script
├── 📄 db.sqlite3                  # ✅ Database (auto-created)
├── 📄 requirements.txt            # ✅ Python dependencies
├── 📄 .env                        # ✅ Environment variables
├── 📄 .env.example                # ✅ Template for .env
├── 📄 .gitignore                  # ✅ Git ignore rules
├── 📄 README.md                   # ✅ Complete documentation
├── 📄 QUICK_START.md              # ✅ Quick start guide
└── 📄 API_INTEGRATION_GUIDE.md    # ✅ Frontend integration
```

## Database Schema

### Authentication Models

#### User (Django Default)
```
┌─────────────────┐
│      User       │
├─────────────────┤
│ id              │ PK
│ username        │ (email)
│ email           │
│ password        │ (not used - OTP)
│ is_active       │
│ is_staff        │
│ date_joined     │
└─────────────────┘
```

#### OTP
```
┌─────────────────┐
│      OTP        │
├─────────────────┤
│ id              │ PK
│ email           │
│ otp_code        │
│ created_at      │
│ is_verified     │
└─────────────────┘
```

#### UserProfile
```
┌─────────────────┐
│  UserProfile    │
├─────────────────┤
│ id              │ PK
│ user_id         │ FK → User
│ phone_number    │
│ created_at      │
│ updated_at      │
└─────────────────┘
```

### Insurance Models

#### InsuranceApplication
```
┌──────────────────────────┐
│  InsuranceApplication    │
├──────────────────────────┤
│ id                       │ PK
│ user_id                  │ FK → User
│ language                 │
│ application_type         │ Employee/Dependent
│ dependent_type           │
│ salary_range             │
│ emirates_id              │ UNIQUE
│ full_name                │
│ date_of_birth            │
│ issuing_date             │
│ expiry_date              │
│ nationality              │
│ gender                   │
│ issuing_place            │
│ occupation               │
│ employer_sponsor_name    │
│ mobile_number            │
│ emirates_id_document     │ FILE
│ status                   │
│ chat_history             │ JSON
│ created_at               │
│ updated_at               │
└──────────────────────────┘
```

#### InsurancePolicy
```
┌──────────────────────────┐
│    InsurancePolicy       │
├──────────────────────────┤
│ id                       │ PK
│ application_id           │ FK → InsuranceApplication
│ policy_number            │ UNIQUE
│ plan_name                │
│ plan_type                │ LSB/NLSB
│ premium_amount           │
│ status                   │ Active/Expired/Cancelled
│ issue_date               │
│ expiry_date              │
│ created_at               │
│ updated_at               │
└──────────────────────────┘
```

#### ChatMessage
```
┌─────────────────┐
│  ChatMessage    │
├─────────────────┤
│ id              │ PK
│ user_id         │ FK → User
│ message_type    │ user/bot
│ content         │ TEXT
│ session_id      │
│ created_at      │
└─────────────────┘
```

## API Endpoints Summary

### 🔐 Authentication (`/api/auth/`)
```
POST   /send-otp/      → Send OTP to email
POST   /verify-otp/    → Verify OTP and login
POST   /logout/        → Logout user
GET    /me/            → Get current user info
GET    /check/         → Check authentication status
```

### 💼 Insurance (`/api/insurance/`)

**Applications**
```
GET    /applications/                    → List all applications
POST   /applications/                    → Create new application
GET    /applications/{id}/               → Get specific application
PUT    /applications/{id}/               → Update application
DELETE /applications/{id}/               → Delete application
GET    /applications/active/             → Get active application
POST   /applications/{id}/update_status/ → Update status
```

**Policies**
```
GET    /policies/           → List user policies
GET    /policies/{id}/      → Get specific policy
GET    /policies/active/    → Get active policies
POST   /create-policy/      → Create new policy
```

**OCR & Recommendations**
```
POST   /process-ocr/        → Upload & process Emirates ID
POST   /recommendations/    → Get product recommendations
```

**Chat**
```
GET    /chat/               → List chat messages
POST   /chat/               → Save chat message
GET    /chat/?session_id=X  → Get messages by session
```

## Business Logic Flow

### Authentication Flow
```
1. User enters email
2. Backend generates 4-digit OTP
3. OTP sent via SMTP email
4. User enters OTP
5. Backend verifies OTP
6. Session created
7. User logged in
```

### Insurance Application Flow
```
1. Language Selection          → Save to state
2. Confirm Medical Insurance   → User choice
3. Employee/Dependent          → Application type
4. Salary Range                → Income bracket
5. Upload Emirates ID          → OCR processing
6. Review & Correct Data       → User verification
7. Get Recommendations         → Product logic
8. Select Product              → User choice
9. Create Policy               → Save to database
10. Success & Redirect         → External URL
```

### Product Recommendation Logic
```
IF issuing_place = "Dubai":
    IF salary < 4000:
        → DHA Basic (LSB) - 864.00 AED
    ELIF salary >= 4000:
        → DHA Basic (LSB) - 864.00 AED
        → DHA Basic (NLSB) - 1893.00 AED

ELIF issuing_place = "Abu Dhabi":
    IF salary > 5000:
        → DHA Basic (NLSB) - 1893.00 AED
    ELSE:
        → No products available

ELSE:
    → DHA Basic (LSB) - 864.00 AED (default)
```

## Key Features Implemented

### ✅ Authentication
- [x] OTP generation (4-digit)
- [x] Email sending via SMTP
- [x] OTP expiry (10 minutes)
- [x] Session management
- [x] User profile creation
- [x] Login/Logout

### ✅ Insurance Management
- [x] Multi-language support
- [x] Employee & Dependent flows
- [x] Emirates ID upload
- [x] OCR data extraction (mock)
- [x] Data validation
- [x] Product recommendations
- [x] Policy creation
- [x] One policy per Emirates ID rule
- [x] Emirates ID expiry check

### ✅ Chat System
- [x] Message storage
- [x] Session-based conversations
- [x] User/Bot message types
- [x] Chat history retrieval

### ✅ Admin Panel
- [x] User management
- [x] OTP logs
- [x] Application tracking
- [x] Policy management
- [x] Chat message review

### ✅ Security
- [x] Session authentication
- [x] CSRF protection
- [x] CORS configuration
- [x] File upload validation
- [x] Email validation
- [x] Business rule enforcement

## Environment Variables

```env
# Django
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Email (SMTP)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Database
DATABASE_NAME=db.sqlite3

# Frontend
FRONTEND_URL=http://127.0.0.1:8000
```

## Tech Stack Details

| Component | Technology | Version |
|-----------|-----------|---------|
| Backend Framework | Django | 5.2.10 |
| API Framework | Django REST Framework | 3.16.1 |
| CORS | django-cors-headers | 4.6.0 |
| Image Processing | Pillow | 11.2.0 |
| Environment | python-dotenv | 1.2.1 |
| Database (Dev) | SQLite3 | Built-in |
| Email | SMTP | Gmail/Custom |
| Authentication | Session-based | Django Sessions |
| Frontend | HTML/CSS/JS | Vanilla + Tailwind |

## File Upload Configuration

```python
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

Allowed Extensions: ['pdf', 'jpg', 'jpeg', 'png']
Upload Path: media/emirates_ids/
```

## Session Configuration

```python
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 86400  # 24 hours
SESSION_SAVE_EVERY_REQUEST = True
```

## CORS Configuration

```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]
CORS_ALLOW_CREDENTIALS = True
```

## Status Codes

| Status | Application | Policy |
|--------|-------------|--------|
| Draft | Initial state | - |
| In Progress | User filling data | - |
| Pending OCR | Document uploaded | - |
| Under Review | Data being verified | - |
| Completed | Application done | - |
| Rejected | Failed validation | - |
| - | - | Active |
| - | - | Expired |
| - | - | Cancelled |

## Next Integration Steps

1. ✅ Backend is ready
2. ✅ Frontend HTML is integrated
3. 🔲 Update JavaScript to use API endpoints
4. 🔲 Test authentication flow
5. 🔲 Test insurance flow
6. 🔲 Add real OCR service
7. 🔲 Add payment gateway
8. 🔲 Deploy to production

---

**Backend Status:** ✅ Fully Functional
**Server Running:** http://127.0.0.1:8000/
**Admin Panel:** http://127.0.0.1:8000/admin/
**API Ready:** Yes
**SMTP Configured:** Console (Dev) / SMTP (Prod)
