# Vulnerable Web Application - Security Education Platform

This is an intentionally vulnerable web application designed for security education purposes. The application contains 8 deliberate vulnerabilities based on the OWASP Top 10 to provide hands-on learning opportunities for students to identify, exploit, and understand common web security flaws.

## Table of Contents
- [Overview](#overview)
- [Vulnerabilities Implemented](#vulnerabilities-implemented)
- [Technology Stack](#technology-stack)
- [Setup and Installation](#setup-and-installation)
- [Running the Application](#running-the-application)
- [Security Testing Exercises](#security-testing-exercises)
- [Educational Purpose](#educational-purpose)
- [Important Security Notice](#important-security-notice)
- [Project Structure](#project-structure)
- [License](#license)

## Overview

The application is a simple web app with user authentication (signup/login) and a dashboard. It is built with FastAPI and SQLite, and intentionally contains security vulnerabilities to serve as a training ground for learning about web application security.

## Vulnerabilities Implemented

1. **SQL Injection** - **FIXED**: Parameterized queries now used in login, signup, and search endpoints (previously used string concatenation in SQL queries)
2. **Stored XSS** - **FIXED**: Username now HTML-escaped before display in dashboard (previously unescaped username displayed on dashboard)
3. **Reflected XSS** - Unescaped query parameter in search endpoint
4. **Session Hijacking** - Hardcoded weak secret key for session signing
5. **Weak Password Storage** - **FIXED**: Now uses bcrypt with work factor >= 12 (previously MD5 without salt)
6. **Exposed Database** - Unauthenticated `/download/db` endpoint
7. **No Rate Limiting** - Absent on all endpoints
8. **CSRF** - Missing token validation on all forms

## Technology Stack

- **Backend**: FastAPI, Uvicorn, Python-Multipart, ItsDangerous
- **Database**: SQLite3
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Session Management**: Starlette SessionMiddleware

## Setup and Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/abdurrahmantaherr/vuln-webapp.git
   cd vuln-webapp
   ```

2. **Set up the Python environment** (using uv):
   ```bash
   uv sync
   ```

3. **Activate the virtual environment**:
   - **Windows**:
     ```bash
     .venv\Scripts\Activate.ps1
     ```
   - **Unix/macOS**:
     ```bash
     source .venv/bin/activate
     ```

## Running the Application

From the project root:
```bash
cd backend
uv run app/main.py
```

The application will start on http://localhost:3001 (or http://127.0.0.1:3001).

### Custom Host and Port

You can customize the host and port using environment variables:

- **Default** (localhost only, more secure for local testing):
  ```bash
  uv run app/main.py
  ```

- **Accessible on all interfaces** (use with caution):
  ```bash
  HOST=0.0.0.0 uv run app/main.py
  ```

- **Custom port**:
  ```bash
  PORT=8080 uv run app/main.py
  ```

- **Both custom host and port**:
  ```bash
  HOST=0.0.0.0 PORT=8080 uv run app/main.py
  ```

Access the application at http://localhost:3001 (or http://127.0.0.1:3001 for default binding).

## Security Testing Exercises

Once the application is running, try these exercises to identify and exploit the intentional vulnerabilities:

### 1. SQL Injection
**Note**: This vulnerability has been FIXED. The following exercises will not work as expected.
- **Login bypass**: Use `admin' --` as username with any password (should now fail)
- **Union-based injection**: Test in search endpoint (should now treat input as literal value)

### 2. Stored XSS
**Note**: This vulnerability has been FIXED. The following exercise will not work as expected.
- **Register** with username: `<script>alert('Stored XSS')</script>`
- **Login** and visit the dashboard to see the script execute (should now see escaped text)

### 3. Reflected XSS
- Visit: `http://localhost:3001/search?query=<script>alert('Reflected XSS')</script>`

### 4. Session Hijacking
- **Inspect cookies** after login to see the session token
- **Weak secret**: The application uses `super-secret-key-12345` for signing
- **Exercise**: Create a session cookie for another user without knowing their password

### 5. Weak Password Storage (FIXED)
- **Note**: This vulnerability has been fixed - passwords are now hashed using bcrypt with work factor >= 12
- **Examine the database** (see below) to see passwords stored as secure bcrypt hashes
- **Exercise**: Attempt to verify that legacy MD5 hashes no longer work and that new bcrypt hashes are secure

### 6. Exposed Database
- Visit: `http://localhost:3001/download/db` to download the SQLite database without authentication
- **Exercise**: Extract password hashes and attempt to crack them

### 7. No Rate Limiting
- **Exercise**: Attempt hundreds of login attempts quickly to test for lack of throttling
- **Exercise**: Brute force weak passwords

### 8. CSRF
- **Exercise**: Create an HTML form on another domain that submits to the application's endpoints
- **Note**: Lack of CSRF tokens allows cross-site request forgery

## Educational Purpose

This application is designed exclusively for security training and education. It should never be deployed to production environments or used on systems without explicit authorization. The vulnerabilities are implemented exactly as specified to allow students to:

- Identify vulnerabilities in source code
- Exploit them using real attack vectors
- Understand root causes at the code level
- Learn and implement secure coding practices

## Important Security Notice

⚠️ **THIS APPLICATION IS INTENTIONALLY VULNERABLE AND MUST NOT BE USED IN PRODUCTION** ⚠️

Do not deploy this application to any public-facing server or use it for any purpose other than authorized security education in isolated, controlled environments.

## Project Structure

```
vuln-webapp/
├── backend/
│   ├── app/
│   │   ├── main.py              # Application entry point
│   │   ├── api/
│   │   │   └── routes/
│   │   │       └── auth.py      # Authentication routes (login/signup/dashboard/search/db download)
│   │   ├── core/
│   │   │   └── security.py      # Password hashing (bcrypt with work factor >= 12 - fixed vulnerability)
│   │   ├── db/
│   │   │   └── session.py       # Database connection and initialization
│   │   └── services/
│   │       └── auth_service.py  # Authentication logic (SQL injection vulnerabilities)
│   ├── .venv/                   # Virtual environment (created by uv)
│   ├── pyproject.toml           # Project dependencies
│   ├── uv.lock                  # Locked dependencies
│   ├── vulnerable_app.db        # SQLite database (created on first run)
│   ├── cookies*.txt             # Testing artifacts (safe to ignore)
│   └── __init__.py files
├── frontend/
│   ├── static/
│   │   ├── css/
│   │   │   └── styles.css       # Styling
│   │   └── images/              # Logos and icons
│   └── templates/               # HTML templates (signup.html, login.html, dashboard.html, etc.)
├── docs/                        # Documentation and prompts
├── .claude/                     # Claude Code specifications and plans
├── .gitignore
├── README.md                    # This file
└── CLAUDE.md                    # Project instructions and vulnerability details
```

## License

This project is provided for educational purposes only. See the [LICENSE](LICENSE) file for details.

## Contributing

This is an educational project. If you find issues or have suggestions for improving the educational value, please open an issue or submit a pull request.

---

**Happy Hacking (Responsibly)!** 🔒📚