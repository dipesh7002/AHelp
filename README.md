# AHelp

AHelp is a Django + Django REST Framework backend for an assignment helper website.

## Tech Stack

- Django
- Django REST Framework
- django-cors-headers
- SQLite for local development

## Setup

```bash
python -m pip install django djangorestframework django-cors-headers python-dotenv
cd core
python manage.py migrate
python manage.py runserver
```

## Auth API

```text
POST  /api/accounts/users/request-otp/
POST  /api/accounts/users/verify-otp/
PATCH /api/accounts/users/profile/

POST  /api/accounts/writers/request-otp/
POST  /api/accounts/writers/verify-otp/
PATCH /api/accounts/writers/profile/

GET   /api/accounts/me/
```

The project uses email OTP login and returns JWT tokens after successful OTP verification.
Writer profile completion requires a CV upload (`cv`, PDF/DOC/DOCX). After submission, the backend emails the writer details and CV attachment to `assignmenthelperr0@gmail.com` by default.
