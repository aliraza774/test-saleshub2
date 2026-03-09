# SalesHub Code Quality & Security Template

This template summarizes the core requirements from `Overview.md` and adds concrete rules for how we design and generate code in SalesHub. Use it as:
- A **checklist** when writing or reviewing code.
- A **prompt helper** when asking an AI assistant to generate or refactor code.

---

## 1. Core Principles

- **Single Source of Truth**: Backend (Django + DRF) is the source of truth for business rules (quote calculation, permissions, status changes).
- **Least Privilege**: Implement and enforce role-based access (Admin, Agent, Viewer, Customer, Company) so users only see and do what they need.
- **Secure by Default**: No open endpoints without explicit justification. Opt-in CORS, HTTPS in production, strong password policies, CSRF where applicable.
- **Auditability**: Important actions (quote creation, updates, authentication events) should be logged in a structured way for later audit.
- **Separation of Concerns**:
  - Django apps are feature-oriented (`accounts`, `companies`, `products`, `quotes`).
  - React uses clear routing and separates page-level containers from reusable UI components.

When prompting an AI, always mention these principles explicitly.

---

## 2. Authentication & Authorization Rules

- **Auth Stack**
  - Backend: Django + Django REST Framework (DRF).
  - Tokens: Prefer JWT (e.g., `SimpleJWT`) for API auth from React.
  - Use Django’s password hashing (PBKDF2 by default), never store raw passwords.

- **User Model**
  - Single `User` model with:
    - `id`, `name`, `email` (unique), `password_hash` (managed by Django), `role`, `status`, timestamps.
  - `role` is an enum with at least: `ADMIN`, `AGENT`, `VIEWER`, `CUSTOMER`, `COMPANY`.
  - `status` indicates active / inactive / suspended.
  - Email is the primary login identifier (no username field exposed to clients).

- **Sign Up / Sign In**
  - Two main sign-up flows:
    - **Customer sign-up** → creates a User with role `CUSTOMER`.
    - **Company sign-up** → creates a User with role `COMPANY` and a linked Company profile when needed.
  - Sign-in accepts email + password and returns JWT tokens (access + refresh).
  - Lock out or throttle after repeated failed login attempts (rate limiting to be added later).

- **Authorization**
  - Use DRF permission classes per view:
    - Admin-only views for sensitive configuration.
    - Role-specific access for quotes, products, and companies.
  - Never trust role information from the client; derive from the authenticated token/session.

When prompting for auth code, clearly specify: **JWT-based auth, email as identifier, role-based access, secure password handling**.

---

## 3. Data & Models (from Overview)

Target tables from the overview:

- **Users**
  - `id | name | email | password_hash | role | status | created_at`

- **Companies**
  - `id | name | logo | contact_email | contact_number | commission | status | created_at`

- **Products**
  - `id | company_id | name | category | base_premium | tax_percentage | commission_percentage | status`

- **Quotes**
  - `id | quote_id | user_id | company_id | product_id | client_name | client_email | coverage_start | coverage_end | base_premium | tax | discount | final_premium | status | created_at`

Modeling rules:

- Use **PostgreSQL** as the primary database in non-local environments.
- Use `UUIDField` or deterministic identifiers for external `quote_id` fields; never expose internal numeric IDs directly in public URLs if avoidable.
- Add `created_at` and `updated_at` timestamps on all core models via an abstract base model.
- Use appropriate field types (`EmailField`, `DecimalField` with explicit precision, `DateField`, `JSONField` for flexible coverage details if needed).

When asking an AI to design models, include:
> “Use PostgreSQL-friendly types, include created_at/updated_at, and align with the Users/Companies/Products/Quotes schema from Overview.md.”

---

## 4. API Design & DRF Conventions

- **Naming & Structure**
  - Base path: `/api/`.
  - Use plural resource names, e.g.:
    - `/api/auth/login/`, `/api/auth/signup/customer/`, `/api/auth/signup/company/`.
    - `/api/companies/`, `/api/products/`, `/api/quotes/`.
  - Use DRF viewsets where CRUD is standard; function-based or APIView where flows are more custom (e.g., quote calculation).

- **Serialization & Validation**
  - Use DRF `Serializer` classes:
    - Validate all input (types, required fields, formats).
    - Enforce email uniqueness in signup.
    - Do not expose sensitive fields (password hashes, internal IDs where not necessary).
  - Perform **business validation** on the backend (e.g., company/product must be active to generate quotes).

- **Error Handling**
  - Use proper HTTP status codes:
    - `400` for validation errors, `401` for unauthenticated, `403` for forbidden, `404` for missing resources.
  - Return structured error responses (`{"detail": "...", "field_errors": {...}}`).

When generating endpoints with AI, always request:
> “Use DRF serializers and permission classes, validate all incoming data, and don’t expose sensitive fields.”

---

## 5. UI & Navigation Guidelines (React)

- **Layout**
  - Sidebar navigation with links: `Dashboard`, `Companies`, `Products`, `Get Quote`, `Sign Out`.
  - Main area for tables, forms, and a quote wizard; top bar for page title and user profile.

- **Auth Pages**
  - Dedicated pages/routes:
    - `/login` – sign-in using email + password.
    - `/signup/customer` – customer registration.
    - `/signup/company` – company registration.
    - `/` or `/landing` – post-login landing page (summary/dashboard).
  - Use form validation on the client but never rely solely on it; all data re-validated on the server.

- **State & Security**
  - Store JWT access tokens in memory or secure HTTP-only cookies (avoid localStorage for long-lived sensitive tokens).
  - Use React Router for navigation and protect private routes based on auth state.

When prompting for React code, mention:
> “Use React Router, form validation, and call the Django/DRF JWT APIs for login and signup.”

---

## 6. Security Checklist

- Passwords:
  - Use Django’s built-in password hashing.
  - Enforce minimum length and complexity via validators.

- Transport:
  - Assume HTTPS in production; do not hardcode `http://` URLs.

- CSRF & CORS:
  - Enable CSRF protection for cookie-based auth.
  - For JWT + SPA, configure CORS (`django-cors-headers`) to only allow known frontend origins.

- Input Validation:
  - Validate all fields server-side.
  - Sanitize or restrict HTML input (if any) to avoid XSS.

- Logging & Auditing:
  - Log authentication attempts (success/failure) and quote-related actions.
  - Avoid logging secrets (passwords, tokens).

When generating security-sensitive code, include:
> “Follow OWASP best practices, use Django’s security features (CSRF, auth, validators), and avoid logging secrets.”

---

## 7. Prompt Template (for AI Code Generation)

When asking an AI to generate code for this project, start with something like:

> “You are working on the *SalesHub Insurance Quote Creation Tool* using Django + DRF (backend, PostgreSQL) and React (frontend).  
> Follow the rules from `template.md` for security, auth, role-based access, and data modeling.  
> Implement [feature] in the `[app_name]` app, exposing RESTful endpoints under `/api/...` and, where relevant, React pages that consume them.  
> Use email for login, JWT auth, DRF serializers, and ensure all inputs are validated server-side.  
> Don’t expose sensitive fields or raw passwords in any response.”

Adjust `[feature]` and `[app_name]` for each task.

