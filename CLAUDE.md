# Vulnerable Web Application - Security Education Platform

This is an intentionally vulnerable web application designed for security education purposes. The application contains 8 deliberate vulnerabilities based on the OWASP Top 10 to provide hands-on learning opportunities for students to identify, exploit, and understand common web security flaws.

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

## Educational Purpose

This application is designed exclusively for security training and education. It should never be deployed to production environments or used on systems without explicit authorization. The vulnerabilities are implemented exactly as specified to allow students to:
- Identify vulnerabilities in source code
- Exploit them using real attack vectors
- Understand root causes at the code level
- Learn and implement secure coding practices

## Usage

The application can be run from any directory after setting up the Python environment:
```bash
# From project root
cd backend
uv sync
.venv\Scripts\Activate.ps1  # Windows
python app/main.py
```

Access the application at http://localhost:3001

## Important Security Notice

⚠️ **THIS APPLICATION IS INTENTIONALLY VULNERABLE AND MUST NOT BE USED IN PRODUCTION** ⚠️