# Implementation Plan: Intentionally Vulnerable Web Application

## Context
This plan outlines the step-by-step implementation of an intentionally vulnerable web application designed for security education. The application contains 8 deliberate vulnerabilities based on OWASP Top 10 to provide hands-on learning opportunities for students to identify, exploit, and understand common web security flaws.

## Phase 1: Project Structure

### Backend Directory Structure
Create the following directory structure and files:
```
backend/
├── app/
│   ├── main.py
│   ├── __init__.py (empty file)
│   ├── core/
│   │   ├── __init__.py (empty file)
│   │   └── security.py
│   ├── db/
│   │   ├── __init__.py (empty file)
│   │   └── session.py
│   ├── services/
│   │   ├── __init__.py (empty file)
│   │   └── auth_service.py
│   └── api/
│       ├── __init__.py (empty file)
│       ├── routes/
│       │   ├── __init__.py (empty file)
│       │   └── auth.py
│       └── __init__.py (empty file)
└── pyproject.toml
```

### Backend Dependencies (pyproject.toml)
Create a `backend/pyproject.toml` file with the following content:
```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "vulnerable-app"
version = "1.0.0"
description = "Intentionally vulnerable web application for security education"
dependencies = [
    "fastapi>=0.109.0",
    "uvicorn>=0.27.0",
    "python-multipart>=0.0.6",
    "itsdangerous>=2.0.0"
]

[project.optional-dependencies]
dev = [
    "pytest"
]
```

### Frontend Directory Structure
Create the following directory structure:
```
frontend/
├── templates/
│   ├── login.html
│   ├── signup.html
│   └── dashboard.html
└── static/
    ├── css/
    │   └── styles.css
    └── images/
        ├── PUCIT_Logo.png (already present)
        ├── blue-logo-scl2.png (already present)
        └── excaliat-logo.png (already present)
```

## Phase 2: Database Layer

### File: backend/app/db/session.py
Implement the database layer with the following specifications:
- Use sqlite3 to connect to `vulnerable_app.db` at the project root
- Implement `get_db()` function that:
  - Creates a connection with `check_same_thread=False`
  - Sets `row_factory` to `sqlite3.Row`
  - Returns the connection object
- Implement `init_db()` function that:
  - Creates the users table if it doesn't exist
  - Uses `CREATE TABLE IF NOT EXISTS` with schema:
    ```sql
    CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        email TEXT,
        password TEXT
    )
    ```
  - Commits the transaction and closes the connection

## Phase 3: Security Utilities

### File: backend/app/core/security.py
Implement security utilities with the following specifications:
- `hash_password(password: str) -> str` function that:
  - Uses `hashlib.md5()` to hash the password
  - Returns the hexadecimal digest
  - **Importantly: Uses NO salt** (vulnerability #5: Weak Password Storage)
- `verify_password(plain: str, hashed: str) -> bool` function that:
  - Compares the MD5 hash of the plain password with the hashed value
  - Returns True if they match, False otherwise

## Phase 4: Business Logic (auth_service.py)

### File: backend/app/services/auth_service.py
Implement authentication service with the following specifications:

#### signup function
- Parameters: `username: str = Form(...)`, `email: str = Form(...)`, `password: str = Form(...)`
- Validates that all fields are present (non-empty)
- Hashes password using `hash_password()` from security.py
- Builds INSERT query using **STRING CONCATENATION** (vulnerability #1: SQL Injection):
  ```python
  query = f"INSERT INTO users (username, email, password) VALUES ('{username}', '{email}', '{hashed_password}')"
  ```
- Executes the query against the database
- On success: Returns `RedirectResponse(url="/login", status_code=303)`
- On UNIQUE constraint error (username already exists): Returns JSON response with `{"error": "Username already exists"}` and status code 409
- On other exceptions: Returns JSON response with error message and status code 500

#### login function
- Parameters: `username: str = Form(...)`, `password: str = Form(...)`
- Validates that both fields are present (non-empty)
- Hashes password using `hash_password()` from security.py
- Builds SELECT query using **STRING CONCATENATION** (vulnerability #1: SQL Injection):
  ```python
  query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{hashed_password}'"
  ```
- Executes the query against the database
- If user found:
  - Returns dictionary with:
    ```python
    {
        "success": True,
        "user_id": result["id"],
        "username": result["username"],
        "email": result["email"],
        "redirect": "/welcome"
    }
    ```
- If user not found:
  - Returns JSON response with `{"error": "Invalid credentials"}` and status code 401

**Critical Implementation Note**: All SQL queries in both `auth_service.py` and `auth.py` MUST use string concatenation (not parameterized queries) to intentionally create the SQL injection vulnerability.

## Phase 5: API Routes

### File: backend/app/api/routes/auth.py
Implement authentication routes with the following specifications:

#### Basic Routes
- `GET /`: Redirects to `/signup`
- `GET /signup`: Serves signup.html template
- `POST /signup`: Processes registration form (calls auth_service.signup)
- `GET /login`: Serves login.html template
- `POST /login`: Processes login form (calls auth_service.login)

#### Protected Route
- `GET /welcome`: 
  - Checks for `user_id` in session (if absent, redirects to `/login`)
  - Retrieves username from session
  - Loads dashboard.html template
  - Performs runtime string substitution: replaces `{{username}}` with actual username from session
  - Returns HTML response

#### Vulnerable Endpoints
- `GET /logout`:
  - Clears session data
  - Redirects to `/login`

- `GET /search`:
  - **No authentication check** (intentional)
  - Accepts `query` parameter via GET
  - Builds SQL query using string concatenation: 
    ```python
    f"SELECT username, email FROM users WHERE username LIKE '%{query}%' OR email LIKE '%{query}%'"
    ```
  - Builds HTML response by directly concatenating results without escaping:
    ```python
    f"<li>{row['username']} ({row['email']})</li>"
    ```
  - Returns HTML response (vulnerability #3: Reflected XSS)

- `GET /download/db`:
  - **No authentication check** (intentional vulnerability #6: Exposed Database)
  - Serves `vulnerable_app.db` file as downloadable attachment
  - Returns 404 if database file doesn't exist

## Phase 6: Main Application

### File: backend/app/main.py
Implement main application with the following specifications:
- Create FastAPI application instance
- Configure SessionMiddleware with:
  - `secret_key="super-secret-key-12345"` (hardcoded weak secret - vulnerability #4: Session Hijacking)
  - `https_only=False` (not setting Secure flag)
  - `same_site="lax"` (not setting to strict)
- Include auth router
- Mount static files directory at `/static/*`
- On startup event: call `init_db()` from session.py to ensure database/table exists
- Configure to run on host `0.0.0.0` and port `3001` (configurable via PORT environment variable)

## Phase 7: Frontend Templates

### File: frontend/templates/login.html
- Implement split-screen layout with gradient background on left, form on right
- Include form with username and password fields
- Implement client-side form submission via Fetch API (AJAX)
- Show error messages in designated area
- Include link to signup page

### File: frontend/templates/signup.html
- Implement split-screen layout identical to login page
- Include form with username, email, password, and confirm password fields
- Implement client-side password match validation (prevents form submission if mismatched)
- Include advisory password strength meter (visual feedback only, does not affect submission)
- Show password mismatch error below confirm password field
- Include link to login page

### File: frontend/templates/dashboard.html
- Include header with application title and three organizational logos (PUCIT, Excaliat, FCCU)
- Implement hero banner with:
  - Title: "Security Vulnerability Lab"
  - Subtitle: "Explore, Exploit, and Learn"
  - User greeting: "Logged in as <strong>{{username}}</strong>" (where {{username}} gets replaced server-side)
  - Profile and logout buttons
- Include mission card describing educational purpose
- Display vulnerabilities section with 8 vulnerability cards, each containing:
  - Colored tag indicating vulnerability type
  - Title
  - Description
- Include process steps section with 3 steps: Explore, Exploit, Learn
- Implement responsive design that adapts to mobile (below 768px)
- Use exact color scheme, typography, spacing, and styling as specified in the design system

## Phase 8: Static Assets

### File: frontend/static/css/styles.css
Implement CSS with the following design system:
- **Color Variables**:
  - Primary: #1a237e (indigo/dark blue)
  - Secondary: #3949ab (lighter blue)
  - Tertiary: #283593 (medium blue)
  - Deep: #0d1b5e (very dark blue)
  - Dashboard background: #eef1f8 (light blue-gray)
  - Surface: #ffffff (white)
- **Text Colors**:
  - Primary: #1e293b (dark slate)
  - Secondary: #475569 (gray)
  - Muted: #64748b (slate gray)
  - Accent: #1a237e (brand primary)
  - On brand: #ffffff (white)
- **Border Radius**:
  - Inputs: 8px
  - Buttons: 8px
  - Cards: 10px
  - Status tags: 6px
- **Shadows**:
  - Header: 0 2px 10px rgba(26,35,126,0.08)
  - Card hover: 0 4px 16px rgba(26,35,126,0.10)
  - Focus glow: 0 0 0 3px rgba(57,73,171,0.12)
- Implement specific layouts for:
  - Login/signup pages (two-column on desktop, single-column on mobile)
  - Dashboard (header, hero banner, mission card, vulnerabilities grid, process steps)
  - Responsive behaviors at 768px breakpoint
- Include styling for vulnerability tag colors:
  - SQLi: #fef9c3 background, #854d0e text
  - XSS: #fee2e2 background, #991b1b text
  - Session: #f3e8ff background, #6b21a8 text
  - Brute: #ffedd5 background, #9a3412 text
  - Crypto: #dcfce7 background, #166534 text
  - Exposed: #dbeafe background, #1e40af text
  - CSRF: #fce7f3 background, #9d174d text

## Vulnerability Implementation Summary

The plan ensures all 8 specified vulnerabilities are implemented exactly as required:

1. **SQL Injection in login and signup**: String concatenation in SQL queries in auth_service.py (both signup and login functions)
2. **Stored XSS via unescaped username on dashboard**: Username stored unsanitized in database, displayed via {{username}} substitution in dashboard.html without escaping
3. **Reflected XSS via unescaped query parameter in search**: Search endpoint directly interpolates query parameter into HTML response without escaping
4. **Session Hijacking via hardcoded weak secret key**: SessionMiddleware uses hardcoded "super-secret-key-12345" as secret key
5. **Weak Password Storage via MD5 without salt**: hash_password() uses plain MD5 with no salt
6. **Exposed Database via unauthenticated /download/db endpoint**: No authentication check on /download/db route
7. **No Rate Limiting on any endpoint**: Absent on all endpoints (login, signup, search, etc.)
8. **CSRF via missing token validation on all forms**: No CSRF tokens validated on POST endpoints (/signup, /login)

## Verification Approach

To verify the implementation meets all requirements:
1. Verify project structure matches specification exactly
2. Confirm pyproject.toml contains correct dependencies
3. Check that all SQL queries use string concatenation (not parameterized)
4. Verify password hashing uses MD5 without salt
5. Confirm session middleware uses hardcoded weak secret
6. Ensure /download/db and /search endpoints lack authentication
7. Verify absence of rate limiting and CSRF protection
8. Confirm frontend templates match visual specifications
9. Validate that username is displayed via {{placeholder}} substitution in dashboard
10. Test that all 8 vulnerabilities can be exploited as described in PRD/TDD

This plan provides a complete blueprint for implementing the intentionally vulnerable web application as specified in the provided documents, focusing exclusively on the planning phase without creating any actual source code files.