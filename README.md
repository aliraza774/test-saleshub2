# SalesHub - Insurance Quote Creation Tool

SalesHub is an internal web platform to help insurance agents and staff manage companies, products, and generate insurance quotes efficiently.

## Backend (Django + DRF + PostgreSQL) Setup

**Prerequisites**
- Python 3.12 (or compatible 3.x)
- PostgreSQL server (for the primary application database) or Docker (recommended)

**1. Create and activate virtual environment**

From the project root:

```bash
python -m venv .venv
# Windows (PowerShell)
.venv\Scripts\Activate.ps1
```

**2. Install dependencies**

```bash
pip install -r requirements.txt
```

**3. Configure database environment variables**

Create a `.env` file in the project root (same folder as `README.md`) with values matching your PostgreSQL setup:

```bash
DB_NAME=saleshub
DB_USER=saleshub
DB_PASSWORD=saleshub
DB_HOST=localhost
DB_PORT=5434
```

**Optional: Run PostgreSQL via Docker (recommended)**

From the project root:

```bash
docker compose up -d db
```

This starts PostgreSQL and exposes it on `localhost:5434` (matches `DB_PORT=5434` above).

**4. Run development server**

```bash
cd backend
python manage.py migrate
python manage.py runserver
```

The server will run at `http://127.0.0.1:8000/`.

### Auth & API endpoints

The `accounts` app exposes authentication endpoints under `/api/`:

- `POST /api/auth/signup/customer/` – customer sign-up (creates a `User` with role `CUSTOMER`).
- `POST /api/auth/signup/company/` – company sign-up (creates a `User` with role `COMPANY`).
- `POST /api/auth/login/` – email + password login, returns JWT access/refresh tokens.
- `GET /api/landing/` – simple authenticated landing endpoint for logged-in users.

Authentication uses **JWT** via `djangorestframework-simplejwt`, and the custom `User` model is email-based with roles (`ADMIN`, `AGENT`, `VIEWER`, `CUSTOMER`, `COMPANY`) and statuses (`ACTIVE`, `INACTIVE`, `SUSPENDED`) as described in `Overview.md`.

### Template-served pages

Django also serves two HTML pages directly (no React required):

| Route | View | Template |
|---|---|---|
| `/` | `AuthPageView` | `accounts/auth.html` — combined sign-in / sign-up page |
| `/dashboard/` | `DashboardPageView` | `accounts/dashboard.html` — post-login dashboard with sidebar |

Both pages use a shared design-token stylesheet (`accounts/static/accounts/theme.css`) with a blue × white theme, DM Sans / DM Serif Display fonts, and Font Awesome icons.

## Project Structure (current)

```
├── Overview.md          – High-level functional overview & requirements
├── README.md            – This file
├── requirements.txt     – Python backend dependencies
├── template.md          – Code quality, security & prompt guidelines
├── Tracked              – Change history
└── backend/
    ├── manage.py
    ├── core/            – Django project settings, root URL conf
    │   ├── settings.py
    │   ├── urls.py
    │   └── wsgi.py / asgi.py
    └── accounts/        – Custom User model, auth views & templates
        ├── models.py        – User (email-based, roles, statuses)
        ├── serializers.py   – SignupSerializer, LoginSerializer
        ├── views.py         – API views + AuthPageView, DashboardPageView
        ├── urls.py          – /api/ routes
        ├── templates/accounts/
        │   ├── auth.html        – Sign-in / sign-up page
        │   └── dashboard.html   – Post-login dashboard
        └── static/accounts/
            └── theme.css        – Shared design tokens
```

## Next Steps (suggested)

- Add company and product management apps and APIs.
- Implement quote calculation, persistence, and PDF/email export workflows.
- Add PDF generation (ReportLab / WeasyPrint) and email dispatch for quotes.
